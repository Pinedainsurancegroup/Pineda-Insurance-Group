import XCTest

final class LoginTests: XCTestCase {
    override func tearDown() {
        XCUIDevice.shared.orientation = .portrait
        super.tearDown()
    }
    func testM3UProviderHTTPRequiresConsentBeforeFixtureLogin() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing"]
        app.launch()
        app.segmentedControls["sourceMode"].buttons["Lista M3U"].tap()
        let server = app.textFields["serverField"]
        XCTAssertTrue(server.waitForExistence(timeout: 10))
        server.tap()
        server.typeText("http://my-vionex.com:8080/get.php?username=fixture&password=fixture-only&type=m3u_plus\n")
        let error = app.staticTexts["loginError"]
        XCTAssertTrue(error.waitForExistence(timeout: 5))
        XCTAssertTrue(error.label.contains("Activa"))
        let consent = app.switches["httpOptIn"]
        XCTAssertEqual(consent.value as? String, "0")
        capture("login-m3u-http-consent-required", app)
        consent.tap()
        XCTAssertEqual(consent.value as? String, "1")
        let connect = app.buttons["connectButton"]
        if !connect.isHittable { app.swipeUp() }
        connect.tap()
        XCTAssertTrue(app.buttons["dashboard-live"].waitForExistence(timeout: 10))
        // A known get.php list imports its account; the UI must show the decoded
        // username instead of the generic "Lista M3U" account label.
        XCTAssertTrue(app.staticTexts["fixture"].exists)
        capture("login-m3u-provider-account-imported", app)
    }
    func testLoginRejectsHTTPBeforeNetworkingAndPreservesPassword() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing"]
        app.launch()
        let server = app.textFields["serverField"]
        XCTAssertTrue(server.waitForExistence(timeout: 10))
        capture("login-portrait", app)
        server.tap(); server.typeText("http://example.com")
        let username = app.textFields["usernameField"]; username.tap(); username.typeText("test")
        let password = app.secureTextFields["passwordField"]; password.tap(); password.typeText("test\n")
        let error = app.staticTexts["loginError"]
        XCTAssertTrue(error.waitForExistence(timeout: 5))
        XCTAssertTrue(error.label.contains("HTTPS"))
        app.buttons["Mostrar contraseña"].tap()
        XCTAssertEqual(app.textFields["passwordField"].value as? String, "test")
        XCUIDevice.shared.orientation = .landscapeLeft
        waitForLandscape(app)
        XCTAssertTrue(server.waitForExistence(timeout: 5))
        capture("login-landscape", app)
    }
    func testReferenceDashboardFitsBothOrientations() {
        let app = fixtureApp()
        XCTAssertTrue(app.buttons["dashboard-live"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["dashboard-movie"].isHittable)
        XCTAssertTrue(app.buttons["dashboard-series"].isHittable)
        capture("home-portrait", app)
        XCUIDevice.shared.orientation = .landscapeLeft
        waitForLandscape(app)
        XCTAssertTrue(app.buttons["dashboard-live"].isHittable)
        XCTAssertTrue(app.buttons["dashboard-movie"].isHittable)
        XCTAssertTrue(app.buttons["dashboard-series"].isHittable)
        XCTAssertTrue(app.buttons["settingsButton"].isHittable)
        capture("home-landscape", app)
    }
    func testFavoritesAndSearchStayConsistent() {
        let app = fixtureApp()
        XCTAssertTrue(app.buttons["dashboard-live"].waitForExistence(timeout: 10))
        app.buttons["dashboard-live"].tap()
        XCTAssertTrue(app.buttons["channel-live:1"].waitForExistence(timeout: 5))
        app.buttons["favorite-live:1"].tap()
        app.buttons["favoriteFilter"].tap()
        XCTAssertTrue(app.buttons["channel-live:1"].exists)
        XCTAssertFalse(app.buttons["channel-live:2"].exists)
        let search = app.textFields["catalogSearch"]
        search.tap(); search.typeText("Noticias")
        XCTAssertTrue(app.staticTexts["Todavía no hay favoritos"].waitForExistence(timeout: 5))
        app.buttons["Borrar búsqueda"].tap()
        XCTAssertTrue(app.buttons["channel-live:1"].waitForExistence(timeout: 5))
        capture("live-favorites", app)
    }
    func testSeriesOpensEpisodes() {
        let app = fixtureApp()
        XCTAssertTrue(app.buttons["dashboard-series"].waitForExistence(timeout: 10))
        app.buttons["dashboard-series"].tap()
        let series = app.buttons["series-series:1"]
        XCTAssertTrue(series.waitForExistence(timeout: 5))
        capture("series-catalog", app)
        series.tap()
        XCTAssertTrue(app.staticTexts["Episodio de muestra 1"].waitForExistence(timeout: 5))
        capture("series-episodes", app)
    }
    func testSavedUserCanSwitchWithoutNetworking() {
        let app = fixtureApp()
        XCTAssertTrue(app.buttons["settingsButton"].waitForExistence(timeout: 10))
        app.buttons["settingsButton"].tap()
        app.buttons["savedAccountsButton"].tap()
        let other = app.buttons["savedAccount-Otra vista previa"]
        XCTAssertTrue(other.waitForExistence(timeout: 5))
        other.tap()
        XCTAssertTrue(app.buttons["dashboard-live"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Otra vista previa"].exists)
    }
    func testCompactHomeMenuOpensAccountInformation() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account"]
        app.launchEnvironment["PIMFLEX_TEST_CONTENT_WIDTH"] = "390"
        app.launch()
        let menu = app.buttons["compactHomeMenu"]
        XCTAssertTrue(menu.waitForExistence(timeout: 10))
        XCTAssertTrue(menu.isHittable)
        menu.tap()
        app.buttons["Mi Información"].tap()
        XCTAssertTrue(app.buttons["Actualizar información"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Vista previa"].exists)
    }
    private func fixtureApp() -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account"]
        app.launch()
        return app
    }
    private func waitForLandscape(_ app: XCUIApplication) {
        let expected = NSPredicate { _, _ in
            app.windows.firstMatch.frame.width > app.windows.firstMatch.frame.height
        }
        let expectation = XCTNSPredicateExpectation(predicate: expected, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [expectation], timeout: 5), .completed)
    }
    private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}

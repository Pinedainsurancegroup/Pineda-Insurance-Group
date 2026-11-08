import XCTest
import UIKit

final class IPadLayoutTests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
        try XCTSkipUnless(UIDevice.current.userInterfaceIdiom == .pad, "iPad layout suite")
        XCUIDevice.shared.orientation = .portrait
    }
    override func tearDown() {
        XCUIDevice.shared.orientation = .portrait
        super.tearDown()
    }
    func testCategoryAndSearchSurviveSidebarChangesOnRotation() {
        let app = fixtureApp()
        app.buttons["dashboard-live"].tap()
        XCTAssertTrue(app.buttons["channel-live:3"].waitForExistence(timeout: 5))
        let picker = app.buttons["categoryPicker"]
        if app.buttons["category-extra"].exists {
            app.buttons["category-extra"].tap()
        } else {
            XCTAssertTrue(picker.waitForExistence(timeout: 5))
            picker.tap()
            app.buttons["Más títulos"].tap()
        }
        XCTAssertTrue(app.buttons["channel-live:3"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["channel-live:1"].exists)
        let search = app.textFields["catalogSearch"]
        search.tap(); search.typeText("Deportes")
        rotate(.landscapeLeft, app: app)
        let sidebarCategory = app.buttons["category-extra"]
        XCTAssertTrue(sidebarCategory.waitForExistence(timeout: 5))
        XCTAssertTrue(sidebarCategory.isSelected)
        XCTAssertEqual(search.value as? String, "Deportes")
        XCTAssertTrue(app.buttons["channel-live:3"].exists)
        app.buttons["Borrar búsqueda"].tap()
        app.buttons["category-sample"].tap()
        XCTAssertTrue(app.buttons["channel-live:1"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["channel-live:3"].exists)
        capture("ipad-categories-landscape")
        rotate(.portrait, app: app)
        XCTAssertTrue(picker.exists || app.buttons["category-sample"].exists)
        XCTAssertTrue(app.buttons["channel-live:1"].exists)
        XCTAssertFalse(app.buttons["channel-live:3"].exists)
        capture("ipad-catalog-portrait")
    }
    func testPosterProportionsAndGridInBothOrientations() {
        let app = fixtureApp()
        app.buttons["dashboard-movie"].tap()
        let first = app.buttons["movie-movie:1"]
        let second = app.buttons["movie-movie:2"]
        XCTAssertTrue(first.waitForExistence(timeout: 5))
        assertPosterGrid(first, second)
        capture("ipad-movies-portrait")
        rotate(.landscapeLeft, app: app)
        XCTAssertTrue(app.buttons["category-all"].waitForExistence(timeout: 5))
        assertPosterGrid(first, second)
        capture("ipad-movies-landscape")
    }
    func testNarrowContentUsesCompactControls() {
        let app = fixtureApp(narrow: true)
        let live = app.buttons["dashboard-live"]
        XCTAssertLessThanOrEqual(live.frame.width, 390)
        XCTAssertTrue(app.buttons["dashboard-movie"].isHittable)
        app.buttons["dashboard-movie"].tap()
        XCTAssertTrue(app.buttons["categoryPicker"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["category-all"].exists)
        let search = app.textFields["catalogSearch"]
        XCTAssertLessThanOrEqual(search.frame.width, 390)
        let favorite = app.buttons["favorite-movie:1"]
        XCTAssertTrue(favorite.waitForExistence(timeout: 5))
        favorite.tap()
        app.buttons["favoriteFilter"].tap()
        XCTAssertTrue(app.buttons["movie-movie:1"].exists)
        XCTAssertFalse(app.buttons["movie-movie:2"].exists)
        rotate(.landscapeLeft, app: app)
        XCTAssertTrue(app.buttons["categoryPicker"].exists)
        XCTAssertTrue(app.buttons["movie-movie:1"].exists)
        XCTAssertFalse(app.buttons["movie-movie:2"].exists)
        capture("ipad-constrained-content-390pt")
    }
    func testMultiscreenSelectionAndAudioSurviveRotation() {
        let app = fixtureApp()
        app.buttons["multiScreenShortcut"].tap()
        let count = app.segmentedControls["multiScreenCount"]
        XCTAssertTrue(count.waitForExistence(timeout: 5))
        count.buttons["4 pantallas"].tap()
        app.buttons["selectChannel-0"].tap()
        let channel = app.buttons["multiChannel-live:1"]
        XCTAssertTrue(channel.waitForExistence(timeout: 5))
        channel.tap()
        let audio = app.buttons["audioSlot-0"]
        XCTAssertTrue(audio.waitForExistence(timeout: 5))
        XCTAssertEqual(audio.value as? String, "Activado")
        rotate(.landscapeLeft, app: app)
        XCTAssertEqual(audio.value as? String, "Activado")
        XCTAssertTrue(app.staticTexts["Canal de muestra"].exists)
        XCTAssertTrue(app.buttons["selectChannel-3"].exists)
        XCTAssertTrue(app.buttons["selectChannel-3"].isHittable)
        XCTAssertLessThanOrEqual(app.buttons["audioSlot-3"].frame.maxY, app.windows.firstMatch.frame.maxY)
        capture("ipad-four-screens-landscape")
        rotate(.portrait, app: app)
        XCTAssertEqual(audio.value as? String, "Activado")
        XCTAssertTrue(app.staticTexts["Canal de muestra"].exists)
    }
    private func fixtureApp(narrow: Bool = false) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account"]
        if narrow { app.launchEnvironment["PIMFLEX_TEST_CONTENT_WIDTH"] = "390" }
        app.launch()
        XCTAssertTrue(app.buttons["dashboard-live"].waitForExistence(timeout: 10))
        return app
    }
    private func assertPosterGrid(_ first: XCUIElement, _ second: XCUIElement) {
        XCTAssertTrue(second.exists)
        XCTAssertEqual(first.frame.height / first.frame.width, 1.5, accuracy: 0.05)
        XCTAssertEqual(first.frame.minY, second.frame.minY, accuracy: 2)
        XCTAssertGreaterThan(second.frame.minX, first.frame.maxX)
    }
    private func rotate(_ orientation: UIDeviceOrientation, app: XCUIApplication) {
        XCUIDevice.shared.orientation = orientation
        let predicate = NSPredicate { _, _ in
            let frame = app.windows.firstMatch.frame
            return orientation.isLandscape ? frame.width > frame.height : frame.height > frame.width
        }
        XCTAssertEqual(XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: predicate, object: nil)], timeout: 8), .completed)
    }
    private func capture(_ name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}

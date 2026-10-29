import XCTest

final class LoginTests: XCTestCase {
    func testLoginRejectsHTTPBeforeNetworking() {
        let app = XCUIApplication(); app.launch()
        let server = app.textFields["serverField"]
        XCTAssertTrue(server.waitForExistence(timeout: 10))
        server.tap(); server.typeText("http://example.com")
        let username = app.textFields["usernameField"]; username.tap(); username.typeText("test")
        let password = app.secureTextFields["passwordField"]; password.tap(); password.typeText("test")
        app.buttons["connectButton"].tap()
        let error = app.staticTexts["loginError"]
        XCTAssertTrue(error.waitForExistence(timeout: 5))
        XCTAssertTrue(error.label.contains("HTTPS"))
    }
}

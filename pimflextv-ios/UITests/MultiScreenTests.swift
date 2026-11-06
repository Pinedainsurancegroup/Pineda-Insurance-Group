import XCTest

final class MultiScreenTests: XCTestCase {
    func testChannelSelectionAndExclusiveAudioSurviveLayoutChange() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account"]
        app.launch()
        let shortcut = app.buttons["multiScreenShortcut"]
        XCTAssertTrue(shortcut.waitForExistence(timeout: 10))
        shortcut.tap()

        let count = app.segmentedControls["multiScreenCount"]
        XCTAssertTrue(count.waitForExistence(timeout: 5))
        count.buttons["4 pantallas"].tap()
        choose("live:1", slot: 0, in: app)
        choose("live:2", slot: 3, in: app)

        let firstAudio = app.buttons["audioSlot-0"]
        let fourthAudio = app.buttons["audioSlot-3"]
        XCTAssertEqual(firstAudio.value as? String, "Activado")
        XCTAssertEqual(fourthAudio.value as? String, "Silenciado")
        fourthAudio.tap()
        XCTAssertEqual(firstAudio.value as? String, "Silenciado")
        XCTAssertEqual(fourthAudio.value as? String, "Activado")

        count.buttons["2 pantallas"].tap()
        XCTAssertFalse(app.buttons["audioSlot-3"].exists)
        XCTAssertEqual(firstAudio.value as? String, "Activado")

        // These DEBUG placeholders prove the test did not start external media.
        XCTAssertTrue(app.staticTexts["Vista previa · sin transmisión"].exists)
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "multi-screen-fixture-selection"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    private func choose(_ channel: String, slot: Int, in app: XCUIApplication) {
        let picker = app.buttons["selectChannel-\(slot)"]
        XCTAssertTrue(picker.waitForExistence(timeout: 5))
        picker.tap()
        let row = app.buttons["multiChannel-\(channel)"]
        XCTAssertTrue(row.waitForExistence(timeout: 5))
        row.tap()
        XCTAssertTrue(picker.waitForExistence(timeout: 5))
    }
}

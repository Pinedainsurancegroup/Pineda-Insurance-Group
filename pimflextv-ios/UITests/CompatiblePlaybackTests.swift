import XCTest

final class CompatiblePlaybackTests: XCTestCase {
    func testMKVActuallyDecodesPausesSeeksAndReopensWithoutNetwork() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account", "--test-mkv-playback"]
        app.launch()
        XCTAssertTrue(app.buttons["dashboard-movie"].waitForExistence(timeout: 10))
        app.buttons["dashboard-movie"].tap()
        let movie = app.buttons["movie-movie:1"]
        XCTAssertTrue(movie.waitForExistence(timeout: 10))
        movie.tap()
        let surface = app.otherElements["compatibleVideoSurface"]
        XCTAssertTrue(surface.waitForExistence(timeout: 10))
        waitUntilPlaying(surface)
        XCTAssertFalse(app.descendants(matching: .any)["playbackWaiting"].exists, "Decoded playback must clear the loading indicator")
        capture("mkv-decoded-video", app)

        let pause = app.buttons["compatiblePlayPause"]
        pause.tap()
        let paused = XCTNSPredicateExpectation(predicate: NSPredicate(format: "label == %@", "Reproducir"), object: pause)
        XCTAssertEqual(XCTWaiter.wait(for: [paused], timeout: 5), .completed)
        let position = app.staticTexts["playbackPosition"]
        let before = seconds(position.label)
        let advancing = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in self.seconds(position.label) > before + 1 }, object: nil)
        advancing.isInverted = true
        XCTAssertEqual(XCTWaiter.wait(for: [advancing], timeout: 1.5), .completed)

        app.buttons["Adelantar 10 segundos"].tap()
        let seeked = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in self.seconds(position.label) >= before + 8 }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [seeked], timeout: 5), .completed)
        capture("mkv-paused-and-seeked", app)
        let selected = seconds(position.label)
        pause.tap()
        waitUntilPlaying(surface)
        let progressed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in self.seconds(position.label) >= selected + 1 }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [progressed], timeout: 5), .completed, "The actual decoder clock must advance past the selected position after resuming")
        app.buttons["playerClose"].tap()
        XCTAssertTrue(movie.waitForExistence(timeout: 5))
        XCTAssertFalse(surface.exists)
        movie.tap()
        waitUntilPlaying(surface)
        XCTAssertLessThan(seconds(position.label), 8, "Reopening creates a fresh player instead of leaving a hidden session running")
        app.buttons["playerClose"].tap()
    }

    private func waitUntilPlaying(_ surface: XCUIElement) {
        let playing = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value == %@", "Reproduciendo"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [playing], timeout: 20), .completed)
    }
    private func seconds(_ clock: String) -> Int {
        let parts = clock.split(separator: ":").compactMap { Int($0) }
        return parts.count == 2 ? parts[0] * 60 + parts[1] : 0
    }
    private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways
        add(attachment)
    }
}

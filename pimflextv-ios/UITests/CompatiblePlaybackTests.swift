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

        revealControls(app)
        let pause = app.buttons["compatiblePlayPause"]
        pause.tap()
        let paused = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value BEGINSWITH %@", "En pausa ·"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [paused], timeout: 5), .completed)
        guard let before = seconds(surface) else { return }
        let advancing = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return true }
            return current > before + 1
        }, object: nil)
        advancing.isInverted = true
        XCTAssertEqual(XCTWaiter.wait(for: [advancing], timeout: 1.5), .completed)

        // The sample lasts five minutes so slow CI accessibility snapshots cannot
        // consume the available seek range before the pause/seek assertions.
        XCTAssertLessThan(before, 280, "The local fixture must leave room for a ten-second seek and playback progress")
        revealControls(app)
        app.buttons["Adelantar 10 segundos"].tap()
        let seeked = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= before + 8
        }, object: nil)
        // Read the persistent video surface: slow accessibility snapshots can
        // outlast the four-second overlay without invalidating the media clock.
        XCTAssertEqual(XCTWaiter.wait(for: [seeked], timeout: 20), .completed)
        capture("mkv-paused-and-seeked", app)
        guard let selected = seconds(surface) else { return }
        revealControls(app)
        pause.tap()
        waitUntilPlaying(surface)
        let progressed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= selected + 1
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [progressed], timeout: 20), .completed, "The actual decoder clock must advance past the selected position after resuming")
        revealControls(app)
        app.buttons["playerClose"].tap()
        XCTAssertTrue(movie.waitForExistence(timeout: 5))
        XCTAssertFalse(surface.exists)
        let reopenedAt = Date()
        movie.tap()
        waitUntilPlaying(surface)
        guard let reopenedSeconds = seconds(surface) else { return }
        let elapsedSinceReopen = Int(Date().timeIntervalSince(reopenedAt).rounded(.up))
        XCTAssertLessThanOrEqual(reopenedSeconds, elapsedSinceReopen + 2, "A fresh player starts at zero; allow the real time spent waiting for CI accessibility snapshots")
        revealControls(app)
        app.buttons["playerClose"].tap()
    }

    private func revealControls(_ app: XCUIApplication) {
        // Start a fresh inactivity window even if the chrome is still visible:
        // it can expire between an accessibility query and the injected tap.
        // Anchor to the stable app window: SwiftUI may replace the reveal
        // element's accessibility snapshot while XCTest injects the gesture.
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
    }

    private func waitUntilPlaying(_ surface: XCUIElement) {
        let playing = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value BEGINSWITH %@", "Reproduciendo ·"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [playing], timeout: 20), .completed)
    }
    private func seconds(_ surface: XCUIElement, file: StaticString = #filePath, line: UInt = #line) -> Int? {
        // A missing/malformed value must fail even during the inverted pause
        // expectation; treating it as zero could falsely pass pause/reopen checks.
        guard let value = surface.value as? String else {
            XCTFail("Video surface has no playback value", file: file, line: line)
            return nil
        }
        let fields = value.components(separatedBy: " · ")
        guard fields.count == 2, ["Reproduciendo", "En pausa", "Cargando"].contains(fields[0]) else {
            XCTFail("Malformed playback status: \(value)", file: file, line: line)
            return nil
        }
        let parts = fields[1].split(separator: ":", omittingEmptySubsequences: false)
        let numbers = parts.compactMap { Int($0) }
        guard (2...3).contains(parts.count), numbers.count == parts.count,
              parts.allSatisfy({ !$0.isEmpty && $0.allSatisfy(\.isNumber) }),
              numbers.allSatisfy({ $0 >= 0 && $0 <= Int(Int32.max) }),
              parts.dropFirst().allSatisfy({ $0.count == 2 }),
              numbers.dropFirst().allSatisfy({ $0 < 60 }) else {
            XCTFail("Malformed playback clock: \(value)", file: file, line: line)
            return nil
        }
        return numbers.reduce(0) { $0 * 60 + $1 }
    }
    private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways
        add(attachment)
    }
}

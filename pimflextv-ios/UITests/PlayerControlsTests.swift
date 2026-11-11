import XCTest

/// Local MP4 playback and explicitly synthetic DEBUG choices exercise separate
/// paths. CompatiblePlaybackTests additionally verifies the bundled MKV decoder.
final class PlayerControlsTests: XCTestCase {
    func testNativeLocalMediaPlaysPausesSeeksAndResumes() {
        let app = openPreviewPlayer(arguments: ["--test-native-playback", "--keep-playback-controls-visible"])
        let surface = app.otherElements["nativeVideoSurface"]
        XCTAssertTrue(surface.waitForExistence(timeout: 10))
        let started = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value BEGINSWITH %@", "Reproduciendo ·"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [started], timeout: 20), .completed)
        XCTAssertFalse(app.descendants(matching: .any)["playerFixture"].exists, "This case must use the bundled MP4, not synthetic playback state")
        XCTAssertFalse(app.descendants(matching: .any)["playbackWaiting"].exists)
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "native-local-playback"; attachment.lifetime = .keepAlways
        add(attachment)

        revealControls(app)
        let pause = app.buttons["playerPlayPause"]
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

        XCTAssertLessThan(before, 280)
        revealControls(app)
        app.buttons["playerSeekForward"].tap()
        let seeked = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= before + 8
        }, object: nil)
        // Allow slow accessibility snapshots while observing the permanent
        // surface; the four-second inactivity assertions below are unchanged.
        XCTAssertEqual(XCTWaiter.wait(for: [seeked], timeout: 20), .completed)
        guard let selected = seconds(surface) else { return }
        revealControls(app)
        pause.tap()
        let playingAgain = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value BEGINSWITH %@", "Reproduciendo ·"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [playingAgain], timeout: 20), .completed)
        let resumed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= selected + 1
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [resumed], timeout: 20), .completed)

        revealControls(app)
        app.buttons["playerOptions"].tap()
        XCTAssertTrue(app.buttons["playerOptionsDone"].waitForExistence(timeout: 3))
        // The sample has one rendition and no subtitle track. Do not invent
        // selectable quality levels or subtitles for a real single-file asset.
        XCTAssertFalse(app.buttons["playerQuality-1"].exists)
        XCTAssertFalse(app.buttons["playerSubtitle-0"].exists)
        app.buttons["playerOptionsDone"].tap()
        revealControls(app)
        app.buttons["playerClose"].tap()
        XCTAssertTrue(app.buttons["movie-movie:1"].waitForExistence(timeout: 5))
    }

    func testNativeLocalAudioAndSubtitleSelectionsReachAVPlayer() {
        let app = openPreviewPlayer(arguments: ["--test-track-selection", "--keep-playback-controls-visible"])
        let surface = app.otherElements["nativeVideoSurface"]
        XCTAssertTrue(surface.waitForExistence(timeout: 10))
        let playing = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value BEGINSWITH %@", "Reproduciendo ·"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [playing], timeout: 20), .completed)
        XCTAssertFalse(app.descendants(matching: .any)["playerFixture"].exists)
        app.buttons["playerOptions"].tap()
        let done = app.buttons["playerOptionsDone"]
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["playerAudio-1"].waitForExistence(timeout: 20))
        XCTAssertTrue(app.buttons["playerSubtitle-1"].waitForExistence(timeout: 20))

        // These are actual bundled AAC/mov_text tracks. The diagnostic reads
        // currentMediaSelection, independently of the requested UI selection.
        let selection = app.descendants(matching: .any)["nativeTrackSelection"]
        XCTAssertTrue(selection.waitForExistence(timeout: 5))
        app.buttons["playerAudio-0"].tap()
        waitForTrackSelection(selection, audio: "spa")
        app.buttons["playerAudio-1"].tap()
        waitForTrackSelection(selection, audio: "eng")
        assertSelected(app.buttons["playerAudio-1"])

        app.buttons["playerSubtitle-0"].tap()
        waitForTrackSelection(selection, audio: "eng", subtitle: "spa")
        assertSelected(app.buttons["playerSubtitle-0"])
        done.tap()
        captureSubtitleAfterProgress("native-subtitle-spanish", surface: surface)

        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        waitForTrackSelection(selection, audio: "eng", subtitle: "spa")
        app.buttons["playerSubtitle-1"].tap()
        waitForTrackSelection(selection, audio: "eng", subtitle: "eng")
        assertSelected(app.buttons["playerSubtitle-1"])
        done.tap()
        captureSubtitleAfterProgress("native-subtitle-english", surface: surface)

        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        app.buttons["playerSubtitle--1"].tap()
        waitForTrackSelection(selection, audio: "eng", subtitle: "off")
        assertSelected(app.buttons["playerSubtitle--1"])
        done.tap()
        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        waitForTrackSelection(selection, audio: "eng", subtitle: "off")
        done.tap()
        app.buttons["playerClose"].tap()
        XCTAssertTrue(app.buttons["movie-movie:1"].waitForExistence(timeout: 5))
    }

    func testControlsHideAfterInactivityAndTapRestoresThem() {
        let app = openPreviewPlayer()
        let close = app.buttons["playerClose"]
        assertRemainsPresent(close, for: 2)
        waitForDisappearance(close)

        app.buttons["playerRevealControls"].tap()
        XCTAssertTrue(close.waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["playerPlayPause"].isHittable)
        // Restoration is already asserted. Start a fresh window for cleanup:
        // slow accessibility snapshots can consume the four-second interval.
        revealControls(app)
        close.tap()
        XCTAssertTrue(app.buttons["movie-movie:1"].waitForExistence(timeout: 5))
    }

    func testLivePreviewDoesNotOfferVODSeeking() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account"]
        app.launch()
        XCTAssertTrue(app.buttons["dashboard-live"].waitForExistence(timeout: 10))
        app.buttons["dashboard-live"].tap()
        let channel = app.buttons["channel-live:1"]
        XCTAssertTrue(channel.waitForExistence(timeout: 10))
        channel.tap()
        XCTAssertTrue(app.buttons["playerClose"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.sliders["playerTimeline"].exists)
        XCTAssertFalse(app.buttons["playerSeekBackward"].exists)
        XCTAssertFalse(app.buttons["playerSeekForward"].exists)
        XCTAssertTrue(app.buttons["playerPlayPause"].isHittable)
    }

    func testInteractionRestartsInactivityWindowEvenWhenPaused() {
        let app = openPreviewPlayer()
        let close = app.buttons["playerClose"]
        assertRemainsPresent(close, for: 2)

        let pause = app.buttons["playerPlayPause"]
        pause.tap()
        XCTAssertEqual(pause.label, "Reproducir")
        // A fresh interaction starts another four-second interval; the previous
        // deadline must not hide controls immediately after pausing.
        assertRemainsPresent(close, for: 2)
        waitForDisappearance(close)

        app.buttons["playerRevealControls"].tap()
        XCTAssertTrue(pause.waitForExistence(timeout: 3))
        XCTAssertEqual(pause.label, "Reproducir")
        pause.tap()
        XCTAssertEqual(pause.label, "Pausar")
    }

    func testOptionsRemainOpenAndRetainSyntheticSelections() {
        let app = openPreviewPlayer()
        app.buttons["playerOptions"].tap()
        let done = app.buttons["playerOptionsDone"]
        XCTAssertTrue(done.waitForExistence(timeout: 3))
        assertSelected(app.buttons["playerQuality-0"])

        app.buttons["playerAudio-1"].tap()
        assertSelected(app.buttons["playerAudio-1"])
        app.buttons["playerSubtitle-0"].tap()
        assertSelected(app.buttons["playerSubtitle-0"])
        app.buttons["playerQuality-1"].tap()
        assertSelected(app.buttons["playerQuality-1"])

        // Options must remain usable beyond the player overlay's timeout.
        assertRemainsPresent(done, for: 4.5)
        done.tap()
        XCTAssertTrue(app.buttons["playerClose"].waitForExistence(timeout: 3))
        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 3))
        assertSelected(app.buttons["playerAudio-1"])
        assertSelected(app.buttons["playerSubtitle-0"])
        assertSelected(app.buttons["playerQuality-1"])

        app.buttons["playerSubtitle--1"].tap()
        assertSelected(app.buttons["playerSubtitle--1"])
        app.buttons["playerQuality-0"].tap()
        assertSelected(app.buttons["playerQuality-0"])
        done.tap()
        waitForDisappearance(app.buttons["playerClose"])
    }

    private func openPreviewPlayer(arguments: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--preview-account"] + arguments
        app.launch()
        XCTAssertTrue(app.buttons["dashboard-movie"].waitForExistence(timeout: 10))
        app.buttons["dashboard-movie"].tap()
        let movie = app.buttons["movie-movie:1"]
        XCTAssertTrue(movie.waitForExistence(timeout: 10))
        movie.tap()
        XCTAssertTrue(app.buttons["playerClose"].waitForExistence(timeout: 5))
        return app
    }

    private func revealControls(_ app: XCUIApplication) {
        // Start a fresh inactivity window only before interacting with controls.
        // Inactivity assertions never call this helper; cleanup may do so after.
        // The app window remains stable while SwiftUI updates player elements.
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
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

    private func assertSelected(_ row: XCUIElement, file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertTrue(row.exists, file: file, line: line)
        XCTAssertEqual(row.value as? String, "Seleccionado", file: file, line: line)
    }

    private func waitForTrackSelection(_ status: XCUIElement, audio: String, subtitle: String? = nil,
                                       file: StaticString = #filePath, line: UInt = #line) {
        let predicate: NSPredicate
        if let subtitle {
            predicate = NSPredicate(format: "value == %@", "audio=\(audio);subtitle=\(subtitle)")
        } else {
            predicate = NSPredicate(format: "value BEGINSWITH %@", "audio=\(audio);subtitle=")
        }
        let selected = XCTNSPredicateExpectation(predicate: predicate, object: status)
        XCTAssertEqual(XCTWaiter.wait(for: [selected], timeout: 20), .completed, file: file, line: line)
    }

    private func captureSubtitleAfterProgress(_ name: String, surface: XCUIElement) {
        guard let before = seconds(surface) else { return }
        // Cues repeat every five seconds. Observe a new cue interval after the
        // sheet closes; the saved image requires visual inspection to establish
        // rendered text, independently of the engine-selection assertions.
        let progressed = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= before + 5
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [progressed], timeout: 20), .completed)
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways
        add(attachment)
    }

    private func assertRemainsPresent(_ element: XCUIElement, for seconds: TimeInterval,
                                      file: StaticString = #filePath, line: UInt = #line) {
        let disappeared = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: element)
        disappeared.isInverted = true
        XCTAssertEqual(XCTWaiter.wait(for: [disappeared], timeout: seconds), .completed, file: file, line: line)
    }

    private func waitForDisappearance(_ element: XCUIElement, file: StaticString = #filePath, line: UInt = #line) {
        let disappeared = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: element)
        // The app interval is four seconds; allow scheduling/accessibility latency.
        XCTAssertEqual(XCTWaiter.wait(for: [disappeared], timeout: 7), .completed, file: file, line: line)
    }
}

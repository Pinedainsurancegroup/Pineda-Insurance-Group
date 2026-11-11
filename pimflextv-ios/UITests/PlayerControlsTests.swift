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
        guard let options = nativeTrackOptions(app),
              let spanishAudio = uniqueFullTrack(options.audio, language: "spa", section: "audio"),
              let englishAudio = uniqueFullTrack(options.audio, language: "eng", section: "audio"),
              let spanishSubtitle = uniqueFullTrack(options.subtitles, language: "spa", section: "subtitles"),
              let englishSubtitle = uniqueFullTrack(options.subtitles, language: "eng", section: "subtitles") else { return }

        // These are actual bundled AAC/mov_text tracks. The diagnostic reads
        // currentMediaSelection, independently of the requested UI selection.
        // AVFoundation may expose additional forced-only subtitle options, so
        // an MP4 stream index cannot identify a language in group.options.
        let selection = app.descendants(matching: .any)["nativeTrackSelection"]
        XCTAssertTrue(selection.waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["playerAudio-\(spanishAudio)"].waitForExistence(timeout: 5))
        app.buttons["playerAudio-\(spanishAudio)"].tap()
        waitForTrackSelection(selection, audio: "spa")
        app.buttons["playerAudio-\(englishAudio)"].tap()
        waitForTrackSelection(selection, audio: "eng")
        assertSelected(app.buttons["playerAudio-\(englishAudio)"])

        XCTAssertTrue(app.buttons["playerSubtitle-\(spanishSubtitle)"].waitForExistence(timeout: 5))
        app.buttons["playerSubtitle-\(spanishSubtitle)"].tap()
        waitForTrackSelection(selection, audio: "eng", subtitle: "spa")
        assertSelected(app.buttons["playerSubtitle-\(spanishSubtitle)"])
        done.tap()
        captureSubtitleAfterProgress("native-subtitle-spanish", surface: surface)

        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        waitForTrackSelection(selection, audio: "eng", subtitle: "spa")
        XCTAssertTrue(app.buttons["playerSubtitle-\(spanishSubtitle)"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["playerAudio-\(englishAudio)"].waitForExistence(timeout: 5))
        assertSelected(app.buttons["playerAudio-\(englishAudio)"])
        assertSelected(app.buttons["playerSubtitle-\(spanishSubtitle)"])
        app.buttons["playerSubtitle-\(englishSubtitle)"].tap()
        waitForTrackSelection(selection, audio: "eng", subtitle: "eng")
        assertSelected(app.buttons["playerSubtitle-\(englishSubtitle)"])
        done.tap()
        captureSubtitleAfterProgress("native-subtitle-english", surface: surface)

        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["playerSubtitle--1"].waitForExistence(timeout: 5))
        app.buttons["playerSubtitle--1"].tap()
        waitForTrackSelection(selection, audio: "eng", subtitle: "off")
        assertSelected(app.buttons["playerSubtitle--1"])
        done.tap()
        app.buttons["playerOptions"].tap()
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        waitForTrackSelection(selection, audio: "eng", subtitle: "off")
        XCTAssertTrue(app.buttons["playerSubtitle--1"].waitForExistence(timeout: 5))
        assertSelected(app.buttons["playerSubtitle--1"])
        XCTAssertTrue(app.buttons["playerAudio--2"].waitForExistence(timeout: 5))
        app.buttons["playerAudio--2"].tap()
        assertSelected(app.buttons["playerAudio--2"])
        done.tap()
        app.buttons["playerOptions"].tap()
        XCTAssertTrue(app.buttons["playerAudio--2"].waitForExistence(timeout: 5))
        assertSelected(app.buttons["playerAudio--2"])
        XCTAssertTrue(app.buttons["playerSubtitle--1"].waitForExistence(timeout: 5))
        assertSelected(app.buttons["playerSubtitle--1"])
        done.tap()
        app.buttons["playerClose"].tap()
        XCTAssertTrue(app.buttons["movie-movie:1"].waitForExistence(timeout: 5))
    }

    func testNativeLocalPlaybackContinuesWithAllControlsHidden() {
        // This real-decoder case deliberately omits keep-playback-controls-visible.
        let app = openPreviewPlayer(arguments: ["--test-native-playback"])
        let surface = app.otherElements["nativeVideoSurface"]
        XCTAssertTrue(surface.waitForExistence(timeout: 10))
        let started = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value BEGINSWITH %@", "Reproduciendo ·"), object: surface)
        XCTAssertEqual(XCTWaiter.wait(for: [started], timeout: 20), .completed)
        XCTAssertFalse(app.descendants(matching: .any)["playerFixture"].exists)
        guard let initial = seconds(surface) else { return }
        let decoding = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= initial + 1
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [decoding], timeout: 20), .completed)

        let identifiers = ["playerClose", "playerOptions", "playerTimeline", "playerPlayPause",
                           "playerSeekBackward", "playerSeekForward", "playerAspect", "playbackPosition"]
        let controls = app.descendants(matching: .any).matching(NSPredicate(format: "identifier IN %@", identifiers))
        let close = app.buttons["playerClose"]
        revealControls(app)
        XCTAssertEqual(controls.count, identifiers.count, "The real VOD must expose its complete control overlay")
        // AX queries above can take time. Start the inactivity observation from
        // a fresh interaction, without touching the player again until it hides.
        revealControls(app)
        assertRemainsPresent(close, for: 2)
        waitForDisappearance(close)
        XCTAssertEqual(controls.count, 0, "Timeline, pause and the remaining overlay must all disappear")
        guard let hiddenAt = seconds(surface) else { return }
        let continued = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let current = self.seconds(surface) else { return false }
            return current >= hiddenAt + 2
        }, object: nil)
        XCTAssertEqual(XCTWaiter.wait(for: [continued], timeout: 10), .completed)
        XCTAssertEqual(controls.count, 0, "Playback progress must not reopen the controls")
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "native-local-controls-hidden"; attachment.lifetime = .keepAlways
        add(attachment)

        revealControls(app)
        XCTAssertTrue(close.waitForExistence(timeout: 3))
        XCTAssertEqual(controls.count, identifiers.count, "A tap must restore the complete overlay")
        revealControls(app)
        close.tap()
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

    private struct NativeTrackOption: Decodable {
        let id: Int
        let language: String
        let forcedOnly: Bool
    }

    private struct NativeTrackOptions: Decodable {
        let audio: [NativeTrackOption]
        let subtitles: [NativeTrackOption]
    }

    private func nativeTrackOptions(_ app: XCUIApplication, file: StaticString = #filePath,
                                    line: UInt = #line) -> NativeTrackOptions? {
        let diagnostic = app.descendants(matching: .any)["nativeTrackOptions"]
        guard diagnostic.waitForExistence(timeout: 5) else {
            XCTFail("AVFoundation option metadata diagnostic is absent", file: file, line: line)
            return nil
        }
        let loaded = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            guard let json = diagnostic.value as? String,
                  let options = try? JSONDecoder().decode(NativeTrackOptions.self, from: Data(json.utf8)) else { return false }
            return !options.audio.isEmpty && !options.subtitles.isEmpty
        }, object: nil)
        let result = XCTWaiter.wait(for: [loaded], timeout: 20)
        XCTAssertEqual(result, .completed, "Both real AVFoundation media-selection groups must load", file: file, line: line)
        guard let json = diagnostic.value as? String else {
            XCTFail("AVFoundation option metadata has no JSON value", file: file, line: line)
            return nil
        }
        let attachment = XCTAttachment(string: json)
        attachment.name = "native-track-options"; attachment.lifetime = .keepAlways
        add(attachment)
        guard result == .completed,
              let options = try? JSONDecoder().decode(NativeTrackOptions.self, from: Data(json.utf8)) else {
            XCTFail("Missing or malformed AVFoundation option metadata: \(json)", file: file, line: line)
            return nil
        }
        for group in [options.audio, options.subtitles] {
            guard group.allSatisfy({ $0.id >= 0 }), Set(group.map(\.id)).count == group.count else {
                XCTFail("AVFoundation option IDs must be nonnegative and unique within each group", file: file, line: line)
                return nil
            }
        }
        func summary(_ group: [NativeTrackOption]) -> String {
            group.map { "\($0.id):\($0.language):\($0.forcedOnly ? "forced-only" : "full")" }.joined(separator: ",")
        }
        print("AVFoundation options: audio=[\(summary(options.audio))]; subtitles=[\(summary(options.subtitles))]")
        return options
    }

    private func uniqueFullTrack(_ options: [NativeTrackOption], language: String, section: String,
                                 file: StaticString = #filePath, line: UInt = #line) -> Int? {
        let matches = options.filter { $0.language == language && !$0.forcedOnly }
        guard matches.count == 1 else {
            XCTFail("Expected exactly one non-forced-only \(language) option in \(section); found \(matches.count)", file: file, line: line)
            return nil
        }
        return matches[0].id
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
        let result = XCTWaiter.wait(for: [selected], timeout: 20)
        var details = ""
        if result != .completed {
            let exists = status.exists
            let actual = exists ? String(describing: status.value) : "<element absent>"
            details = "AVPlayer selection was not confirmed: expected audio=\(audio);subtitle=\(subtitle ?? "<any>"); diagnostic exists=\(exists), value=\(actual)"
        }
        XCTAssertEqual(result, .completed, details, file: file, line: line)
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

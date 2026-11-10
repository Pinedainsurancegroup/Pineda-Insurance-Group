import Foundation
import XCTest
@testable import PimflexCore

final class PlaybackRoutingTests: XCTestCase {
    func testMovieAndEpisodeContainersKeepTheirActualExtensionAndUseCompatiblePlayback() throws {
        let account = Account(mode: .xtream, server: URL(string: "https://example.com/tenant")!, username: "u+/#", password: "p? ñ")
        for kind in [MediaKind.movie, .series] {
            for ext in ["mkv", "AVI", "flv", "wmv", "webm"] {
                let url = try Endpoint.playback(account, item: MediaItem(providerID: "42", name: "Fixture", kind: kind, fileExtension: ext))
                XCTAssertTrue(url.path.hasSuffix("42.\(ext.lowercased())"))
                XCTAssertEqual(PlaybackEngine.forMediaURL(url), .compatible)
                XCTAssertNil(url.query)
                XCTAssertNil(url.fragment)
                XCTAssertTrue(url.absoluteString.contains("u%2B%2F%23"))
            }
        }
    }
    func testNativeFormatsAndLiveHLSKeepExistingPlayback() throws {
        let account = Account(mode: .xtream, server: URL(string: "https://example.com")!, username: "fixture", password: "fixture-only")
        for ext in ["mp4", "m4v", "mov", "m3u8", "m4a", "aac"] {
            XCTAssertEqual(PlaybackEngine.forMediaURL(try Endpoint.playback(account, item: MediaItem(providerID: "7", name: "Fixture", kind: .movie, fileExtension: ext))), .native)
        }
        let live = try Endpoint.playback(account, item: MediaItem(providerID: "7", name: "Fixture", kind: .live, fileExtension: "ts"))
        XCTAssertTrue(live.path.hasSuffix("7.m3u8"))
        XCTAssertEqual(PlaybackEngine.forMediaURL(live), .native)
        XCTAssertThrowsError(try Endpoint.playback(account, item: MediaItem(providerID: "7", name: "Bad", kind: .movie, fileExtension: "mkv/../../other")))
    }
    func testDirectPlaylistMKVAndTSRequireExistingHTTPConsent() throws {
        let account = Account(mode: .m3u, server: URL(string: "http://my-vionex.com:8080/list.m3u")!, allowingInsecureHTTP: true)
        for ext in ["mkv", "ts"] {
            let url = URL(string: "http://my-vionex.com:8080/fixture.\(ext)")!
            let item = MediaItem(providerID: ext, name: "Fixture", kind: .movie, directURL: url)
            XCTAssertEqual(try Endpoint.playback(account, item: item), url)
            XCTAssertEqual(PlaybackEngine.forMediaURL(url), .compatible)
            let denied = Account(mode: .m3u, server: account.server)
            XCTAssertThrowsError(try Endpoint.playback(denied, item: item))
        }
    }
    func testCompatibleContainersDoNotAdmitLocalFilesOrCredentialAuthority() {
        let account = Account(mode: .m3u, server: URL(string: "https://example.com/list.m3u")!)
        for raw in ["file:///tmp/fixture.mkv", "https://user:secret@example.com/fixture.mkv", "http://other.example/fixture.mkv"] {
            let item = MediaItem(providerID: "1", name: "Fixture", kind: .movie, directURL: URL(string: raw)!)
            XCTAssertThrowsError(try Endpoint.playback(account, item: item))
        }
    }
}

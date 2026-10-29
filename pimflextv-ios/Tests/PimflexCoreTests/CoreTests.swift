import XCTest
@testable import PimflexCore

final class CoreTests: XCTestCase {
    private var account: Account { Account(mode: .xtream, server: URL(string: "https://example.com/panel")!, username: "u+&/#", password: "p? /ñ") }
    private func data(_ string: String) -> Data { Data(string.utf8) }

    func testRejectsInsecureAndAmbiguousServers() throws {
        for text in ["http://example.com", "file:///etc/test", "https://u:p@example.com", "https://example.com?secret=value", "https://example.com/#fragment"] {
            XCTAssertThrowsError(try Endpoint.server(text), text)
        }
        XCTAssertEqual(try Endpoint.server(" https://example.com/panel/ ").absoluteString, "https://example.com/panel")
        XCTAssertNoThrow(try Endpoint.server("https://example.com/get.php?token=a", playlist: true))
    }
    func testCredentialsStaySeparateQueryValues() throws {
        let url = try Endpoint.api(account, action: "get_live_streams")
        let query = URLComponents(url: url, resolvingAgainstBaseURL: false)!.queryItems!
        XCTAssertEqual(query.first { $0.name == "username" }?.value, account.username)
        XCTAssertEqual(query.first { $0.name == "password" }?.value, account.password)
        XCTAssertEqual(query.count, 3)
        XCTAssertTrue(url.absoluteString.contains("%2B"))
        XCTAssertFalse(URLComponents(url: url, resolvingAgainstBaseURL: false)!.percentEncodedQuery!.contains("+"))
        XCTAssertEqual(url.path, "/panel/player_api.php")
    }
    func testPlaybackEscapesEveryCredentialPathComponent() throws {
        let item = MediaItem(providerID: "42", name: "Channel", kind: .live)
        let url = try Endpoint.playback(account, item: item)
        let path = URLComponents(url: url, resolvingAgainstBaseURL: false)!.percentEncodedPath
        XCTAssertTrue(path.contains("u%2B%26%2F%23"))
        XCTAssertTrue(path.contains("p%3F%20%2F%C3%B1"))
        XCTAssertTrue(path.hasSuffix("/42.m3u8"))
        XCTAssertNil(url.query); XCTAssertNil(url.fragment)
        XCTAssertThrowsError(try Endpoint.playback(account, item: MediaItem(providerID: "../42", name: "Bad", kind: .movie)))
        XCTAssertThrowsError(try Endpoint.playback(account, item: MediaItem(providerID: "42", name: "MKV", kind: .movie, fileExtension: "mkv")))
    }
    func testAuthenticationMustBeActive() throws {
        XCTAssertEqual(try CatalogParser.authenticate(data(#"{"user_info":{"auth":1,"status":"Active","exp_date":"1800000000"}}"#)), "1800000000")
        XCTAssertThrowsError(try CatalogParser.authenticate(data(#"{"user_info":{"auth":0,"status":"Active"}}"#)))
        XCTAssertThrowsError(try CatalogParser.authenticate(data(#"{"user_info":{"auth":"1","status":"Expired"}}"#)))
        XCTAssertThrowsError(try CatalogParser.authenticate(data("[]")))
    }
    func testCatalogHandlesNumericAndStringIDsAndDeduplicates() throws {
        let rows = try CatalogParser.items(data(#"[{"stream_id":7,"name":"Uno","category_id":2},{"stream_id":"7","name":"Duplicado"},{"stream_id":"8","name":"Dos","container_extension":"mkv"}]"#), kind: .movie)
        XCTAssertEqual(rows.count, 2); XCTAssertEqual(rows[0].categoryID, "2"); XCTAssertEqual(rows[1].fileExtension, "mkv")
        let groups = try CatalogParser.categories(data(#"[{"category_id":2,"category_name":"TV"},{"category_id":"2","category_name":"Duplicate"}]"#))
        XCTAssertEqual(groups.count, 1)
    }
    func testEpisodesAreOrderedNumerically() throws {
        let episodes = try CatalogParser.episodes(data(#"{"episodes":{"10":[{"id":10,"title":"Ten","episode_num":1}],"2":[{"id":"22","title":"Second","episode_num":"2"},{"id":"21","title":"First","episode_num":1}]}}"#))
        XCTAssertEqual(episodes.map(\.providerID), ["21", "22", "10"])
        XCTAssertEqual(episodes[0].season, 2)
        let url = try Endpoint.playback(account, item: episodes[0])
        XCTAssertTrue(url.path.contains("/series/")); XCTAssertTrue(url.path.hasSuffix("21.mp4"))
    }
    func testM3UQuotesRelativePathsBOMAndDuplicates() throws {
        let text = "\u{feff}#EXTM3U\r\n#EXTINF:-1 group-title=\"News, World\" tvg-logo=\"https://img.example.com/a.png\",Canal, uno\r\nstream.m3u8\r\n#EXTINF:-1,Duplicate\nstream.m3u8\n#EXTINF:-1,Movie\nhttps://example.com/movie.mp4\n#EXTINF:-1,Unsafe\nhttp://example.com/unsafe.ts\n"
        let entries = try M3UParser.parse(text, baseURL: URL(string: "https://example.com/lists/list.m3u")!)
        XCTAssertEqual(entries.count, 2); XCTAssertEqual(entries[0].name, "Canal, uno")
        XCTAssertEqual(entries[0].categoryID, "News, World")
        XCTAssertEqual(entries[0].directURL?.absoluteString, "https://example.com/lists/stream.m3u8")
        XCTAssertEqual(entries[1].kind, .movie)
    }
    func testHLSIsOneStreamNotSegments() throws {
        let url = URL(string: "https://example.com/master.m3u8")!
        let entries = try M3UParser.parse("#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\na.ts\n#EXTINF:10,\nb.ts", baseURL: url)
        XCTAssertEqual(entries.count, 1); XCTAssertEqual(entries[0].directURL, url)
    }
    func testEmptyAndHTMLPlaylistsFail() {
        let url = URL(string: "https://example.com/list")!
        XCTAssertThrowsError(try M3UParser.parse("<html>Login</html>", baseURL: url))
        XCTAssertThrowsError(try M3UParser.parse("#EXTM3U\n", baseURL: url))
    }
    func testEPGDecodesBase64AndTimestamp() throws {
        let rows = try EPGParser.parse(data(#"{"epg_listings":[{"id":"1","title":"Tm90aWNpYXM=","description":"SG9sYQ==","start_timestamp":"1700000000","stop_timestamp":1700003600}]}"#))
        XCTAssertEqual(rows.first?.title, "Noticias"); XCTAssertEqual(rows.first?.description, "Hola")
        XCTAssertEqual(rows.first?.start?.timeIntervalSince1970, 1700000000)
    }
    func testPreferencesAreIsolatedByAccountWithoutRawCredentials() {
        let other = Account(mode: .xtream, server: account.server, username: "other", password: "secret")
        XCTAssertNotEqual(account.storageID, other.storageID)
        XCTAssertEqual(account.storageID.count, 64)
        XCTAssertFalse(account.storageID.contains(account.username))
    }
    func testRedirectCannotLeakAccountToOtherOrigin() {
        let original = URL(string: "https://example.com/api?password=private")!
        XCTAssertTrue(SafeRedirects.permits(from: original, to: URL(string: "https://example.com/next")!))
        XCTAssertFalse(SafeRedirects.permits(from: original, to: URL(string: "https://attacker.example/next")!))
        XCTAssertFalse(SafeRedirects.permits(from: original, to: URL(string: "http://example.com/next")!))
        XCTAssertFalse(SafeRedirects.permits(from: original, to: URL(string: "https://example.com:8443/next")!))
    }
}

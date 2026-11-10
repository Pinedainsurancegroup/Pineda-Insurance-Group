import Foundation
import XCTest
@testable import PimflexCore

final class CompatibilityTests: XCTestCase {
    private func data(_ text: String) -> Data { Data(text.utf8) }

    func testPastedPortalAddressesKeepTheTenantPathAndSeparateCredentials() throws {
        for route in ["login.php", "player_api.php", "GET.PHP"] {
            let base = try Endpoint.server(" https://example.com:8443/tenant%2Fshared/\(route)/?username=old&password=old ")
            XCTAssertEqual(base.absoluteString, "https://example.com:8443/tenant%2Fshared")
            let account = Account(mode: .xtream, server: base, username: "current+name", password: "a&b")
            let url = try Endpoint.api(account)
            let parts = try XCTUnwrap(URLComponents(url: url, resolvingAgainstBaseURL: false))
            XCTAssertEqual(parts.percentEncodedPath, "/tenant%2Fshared/player_api.php")
            XCTAssertEqual(parts.queryItems?.first(where: { $0.name == "username" })?.value, "current+name")
            XCTAssertEqual(parts.queryItems?.first(where: { $0.name == "password" })?.value, "a&b")
        }
        XCTAssertEqual(try Endpoint.server("https://example.com/my-login.php").path, "/my-login.php")
        XCTAssertEqual(try Endpoint.server("https://example.com/login.php/tenant").path, "/login.php/tenant")
        let playlist = "https://example.com/get.php?username=name&password=p%2Bq&type=m3u_plus"
        XCTAssertEqual(try Endpoint.server(playlist, playlist: true).absoluteString, playlist)
    }

    func testLoadedAccountsAndPlaylistURLsCannotBypassHTTPSValidation() throws {
        let insecure = Account(mode: .xtream, server: URL(string: "http://example.com")!, username: "user", password: "secret")
        let item = MediaItem(providerID: "12", name: "Channel", kind: .live)
        XCTAssertThrowsError(try Endpoint.api(insecure))
        XCTAssertThrowsError(try Endpoint.playback(insecure, item: item))
        let direct = MediaItem(providerID: "12", name: "Channel", kind: .live, directURL: URL(string: "https://user:secret@example.com/live.m3u8")!)
        XCTAssertThrowsError(try Endpoint.playback(insecure, item: direct))
        XCTAssertThrowsError(try Endpoint.server("https://example.com:70000"))
        let origin = URL(string: "https://example.com")!
        XCTAssertFalse(SafeRedirects.permits(from: origin, to: URL(string: "https:relative")!))
        XCTAssertFalse(SafeRedirects.permits(from: origin, to: URL(string: "https://name:secret@example.com/next")!))
        XCTAssertFalse(SafeRedirects.permits(from: URL(string: "http://example.com")!, to: origin))
    }

    func testProviderAuthenticationAcceptsTypedValuesButRequiresActiveStatus() throws {
        XCTAssertEqual(try CatalogParser.authenticate(data(#"{"user_info":{"auth":true,"status":" ACTIVE ","exp_date":null}}"#)), "")
        XCTAssertEqual(try CatalogParser.authenticate(data(#"{"user_info":{"auth":" 1 ","status":"Active","exp_date":1800000000}}"#)), "1800000000")
        XCTAssertThrowsError(try CatalogParser.authenticate(data(#"{"user_info":{"auth":false,"status":"Active"}}"#)))
        XCTAssertThrowsError(try CatalogParser.authenticate(data(#"{"user_info":{"auth":true,"status":"Disabled"}}"#)))
    }

    func testPartialAndIndexedCatalogsKeepValidRowsAndFallbackArtwork() throws {
        let rows = try CatalogParser.items(data(#"[null,"bad",{}, {"stream_id":" 7 ","name":" Film ","category_id":3,"stream_icon":null,"cover":"https://example.com/cover.png","container_extension":" .MP4 "},{"stream_id":7,"name":"Duplicate"}]"#), kind: .movie)
        XCTAssertEqual(rows.count, 1)
        XCTAssertEqual(rows.first?.providerID, "7")
        XCTAssertEqual(rows.first?.name, "Film")
        XCTAssertEqual(rows.first?.fileExtension, "mp4")
        XCTAssertEqual(rows.first?.artwork?.absoluteString, "https://example.com/cover.png")
        let groups = try CatalogParser.categories(data(#"{"10":{"category_id":10,"category_name":"Ten"},"2":{"category_id":"2","category_name":"Two"}}"#))
        XCTAssertEqual(groups.map(\.id), ["2", "10"])
        XCTAssertTrue(try CatalogParser.items(data("{}"), kind: .movie).isEmpty)
        XCTAssertThrowsError(try CatalogParser.items(data(#"{"user_info":{"auth":0}}"#), kind: .live))
    }

    func testEpisodeShapesAndDuplicatesHaveDeterministicSeasonOrder() throws {
        XCTAssertTrue(try CatalogParser.episodes(data(#"{"episodes":[]}"#)).isEmpty)
        XCTAssertTrue(try CatalogParser.episodes(data(#"{"episodes":{}}"#)).isEmpty)
        let indexed = try CatalogParser.episodes(data(#"{"episodes":[null,[{"id":12,"title":"First","episode_num":" 1 "}], [{"id":"22","title":"Second","episode_num":2,"season":"2"}]]}"#))
        XCTAssertEqual(indexed.map(\.season), [1, 2])
        let flat = try CatalogParser.episodes(data(#"{"episodes":[null,{"id":44,"title":"Fourth","season":"3","episode_num":4}]}"#))
        XCTAssertEqual(flat.first?.season, 3)
        let duplicated = try CatalogParser.episodes(data(#"{"episodes":{"10":[{"id":9,"title":"Later duplicate","episode_num":1}],"2":[{"id":9,"title":"Original","episode_num":1}]}}"#))
        XCTAssertEqual(duplicated.count, 1)
        XCTAssertEqual(duplicated.first?.name, "Original")
        XCTAssertEqual(duplicated.first?.season, 2)
    }

    func testM3USingleQuotesNamesAndGroupsDoNotAdmitCredentialAuthorityURLs() throws {
        let text = """
        #EXTM3U
        #EXTINF:-1 group-title='News, World' tvg-name='Canal Uno',
        one.m3u8
        #EXTINF:-1,Canal Dos
        #EXTGRP:Deportes
        two.m3u8
        #EXTINF:-1,Invalid
        https://name:secret@example.com/three.m3u8
        """
        let items = try M3UParser.parse(text, baseURL: URL(string: "https://example.com/lists/catalog.m3u")!)
        XCTAssertEqual(items.count, 2)
        XCTAssertEqual(items[0].name, "Canal Uno")
        XCTAssertEqual(items[0].categoryID, "News, World")
        XCTAssertEqual(items[1].categoryID, "Deportes")
    }

    func testHLSDetectionRequiresAnActualTagAndGuideDatesAreFinite() throws {
        let items = try M3UParser.parse("#EXTM3U\n#EXTINF:-1,A title mentioning #EXT-X-TARGETDURATION\nhttps://example.com/channel.m3u8", baseURL: URL(string: "https://example.com/list.m3u")!)
        XCTAssertEqual(items.first?.directURL?.lastPathComponent, "channel.m3u8")
        XCTAssertThrowsError(try M3UParser.parse("#EXTM3Ubroken\nhttps://example.com/a", baseURL: URL(string: "https://example.com/list")!))
        let guide = try EPGParser.parse(data(#"{"epg_listings":[{"title":"News","start_timestamp":"NaN","stop_timestamp":"Infinity"}]}"#))
        XCTAssertNil(guide.first?.start)
        XCTAssertNil(guide.first?.end)
    }

    func testPlaylistUsesFinalResponseURLForRelativeStreams() async throws {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [PlaylistResponseProtocol.self]
        let session = URLSession(configuration: config)
        defer { session.invalidateAndCancel() }
        let client = APIClient(session: session)
        let account = Account(mode: .m3u, server: URL(string: "https://example.com/playlist")!)
        let items = try await client.playlist(account)
        XCTAssertEqual(items.first?.directURL?.absoluteString, "https://example.com/final/catalog/channel.m3u8")
    }

    func testPlaylistRefusesAnUnexpectedCrossOriginResponse() async throws {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [PlaylistResponseProtocol.self]
        let session = URLSession(configuration: config)
        defer { session.invalidateAndCancel() }
        let client = APIClient(session: session)
        let account = Account(mode: .m3u, server: URL(string: "https://example.com/cross-origin")!)
        do {
            _ = try await client.playlist(account)
            XCTFail("An unexpected response origin must not become the playlist base")
        } catch {
            XCTAssertEqual(error as? PimflexError, .invalidResponse)
        }
    }
}

// A completed HTTP response fixture, with no network or real provider credentials.
private final class PlaylistResponseProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { request.url?.host == "example.com" }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let host = request.url?.path == "/cross-origin" ? "different.example.com" : "example.com"
        let final = URL(string: "https://\(host)/final/catalog/index.m3u")!
        let response = HTTPURLResponse(url: final, statusCode: 200, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "audio/x-mpegurl"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Data("#EXTM3U\n#EXTINF:-1,Channel\nchannel.m3u8\n".utf8))
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() { }
}

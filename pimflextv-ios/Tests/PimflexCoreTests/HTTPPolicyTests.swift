import Foundation
import XCTest
@testable import PimflexCore

final class HTTPPolicyTests: XCTestCase {
    func testProviderHTTPRequiresExplicitExactHostOptIn() throws {
        let portal = "http://moonspelltools.cc:2082/login.php"
        XCTAssertThrowsError(try Endpoint.server(portal))
        XCTAssertEqual(try Endpoint.server(portal, allowingInsecureHTTP: true).absoluteString, "http://moonspelltools.cc:2082")
        for address in ["http://example.com", "http://www.moonspelltools.cc", "http://cdn.moonspelltools.cc:2082", "http://moonspelltools.cc.example.com", "http://moonspelltools.cc.:2082"] {
            XCTAssertThrowsError(try Endpoint.server(address, allowingInsecureHTTP: true), address)
        }
        XCTAssertNoThrow(try Endpoint.server("https://example.com", allowingInsecureHTTP: true))
    }

    func testOldAccountsDecodeWithHTTPDisabledAndOptInSurvivesRoundTrip() throws {
        let oldJSON = Data(#"{"mode":"xtream","server":"http://moonspelltools.cc:2082","username":"test","password":"fixture"}"#.utf8)
        let oldAccount = try JSONDecoder().decode(Account.self, from: oldJSON)
        XCTAssertNil(oldAccount.allowingInsecureHTTP)
        XCTAssertFalse(oldAccount.insecureHTTPEnabled)
        XCTAssertThrowsError(try Endpoint.api(oldAccount))
        let account = Account(mode: .xtream, server: oldAccount.server, username: "test", password: "fixture", allowingInsecureHTTP: true)
        let restored = try JSONDecoder().decode(Account.self, from: JSONEncoder().encode(account))
        XCTAssertTrue(restored.insecureHTTPEnabled)
        XCTAssertEqual(try Endpoint.api(restored).path, "/player_api.php")
        let channel = MediaItem(providerID: "12", name: "Fixture", kind: .live)
        XCTAssertEqual(try Endpoint.playback(restored, item: channel).scheme, "http")
        let direct = MediaItem(providerID: "12", name: "Fixture", kind: .live, directURL: URL(string: "http://moonspelltools.cc:2082/live.m3u8")!)
        XCTAssertThrowsError(try Endpoint.playback(oldAccount, item: direct))
        XCTAssertNoThrow(try Endpoint.playback(restored, item: direct))
    }

    func testHTTPOptInCannotDowngradeHTTPSOrChangeRedirectOrigin() {
        let http = URL(string: "http://moonspelltools.cc:2082/list")!
        let next = URL(string: "http://moonspelltools.cc:2082/next")!
        XCTAssertFalse(SafeRedirects.permits(from: http, to: next))
        XCTAssertTrue(SafeRedirects.permits(from: http, to: next, allowingInsecureHTTP: true))
        XCTAssertFalse(SafeRedirects.permits(from: URL(string: "https://moonspelltools.cc:2082/list")!, to: next, allowingInsecureHTTP: true))
        for address in ["http://other.example/next", "http://cdn.moonspelltools.cc:2082/next", "http://moonspelltools.cc:8080/next", "https://moonspelltools.cc:2082/next"] {
            XCTAssertFalse(SafeRedirects.permits(from: http, to: URL(string: address)!, allowingInsecureHTTP: true), address)
        }
    }

    func testM3UAndArtworkApplyTheSameNarrowOptIn() throws {
        let text = """
        #EXTM3U
        #EXTINF:-1 tvg-logo="http://moonspelltools.cc:2082/logo.png",Original
        http://moonspelltools.cc:2082/channel.m3u8
        #EXTINF:-1,Other host
        http://cdn.moonspelltools.cc:2082/channel.m3u8
        #EXTINF:-1,Secure
        https://example.com/channel.m3u8
        """
        let base = URL(string: "https://example.com/list.m3u")!
        XCTAssertEqual(try M3UParser.parse(text, baseURL: base).count, 1)
        let allowed = try M3UParser.parse(text, baseURL: base, allowingInsecureHTTP: true)
        XCTAssertEqual(allowed.count, 2)
        XCTAssertEqual(allowed.first?.artwork?.scheme, "http")
        let json = Data(#"[{"stream_id":1,"name":"Original","stream_icon":"http://moonspelltools.cc:2082/logo.png"},{"stream_id":2,"name":"Other","stream_icon":"http://cdn.moonspelltools.cc:2082/logo.png"}]"#.utf8)
        XCTAssertNil(try CatalogParser.items(json, kind: .live).first?.artwork)
        let items = try CatalogParser.items(json, kind: .live, allowingInsecureHTTP: true)
        XCTAssertNotNil(items[0].artwork)
        XCTAssertNil(items[1].artwork)
    }

    func testOptedInAccountReachesOnlyTheInjectedHTTPTransport() async throws {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [HTTPPolicyFixtureProtocol.self]
        let session = URLSession(configuration: config)
        defer { session.invalidateAndCancel() }
        let client = APIClient(session: session)
        let url = URL(string: "http://moonspelltools.cc:2082")!
        let allowed = Account(mode: .xtream, server: url, username: "test", password: "fixture", allowingInsecureHTTP: true)
        let expiry = try await client.authenticate(allowed)
        XCTAssertEqual(expiry, "1800000000")
        do {
            _ = try await client.authenticate(Account(mode: .xtream, server: url, username: "test", password: "fixture"))
            XCTFail("An account without opt-in must fail before HTTP transport")
        } catch { XCTAssertEqual(error as? PimflexError, .insecureURL) }
    }
}

// Intercepts EVERY request from this test session. No request can reach a backend.
private final class HTTPPolicyFixtureProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        guard let url = request.url, url.scheme == "http", url.host == "moonspelltools.cc", url.port == 2082 else {
            client?.urlProtocol(self, didFailWithError: URLError(.badURL)); return
        }
        let response = HTTPURLResponse(url: url, statusCode: 200, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Data(#"{"user_info":{"auth":1,"status":"Active","exp_date":"1800000000"}}"#.utf8))
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() { }
}

import Foundation
import XCTest
@testable import PimflexCore

final class PlaylistAccountImportTests: XCTestCase {
    func testProviderListAuthenticatesThroughAPIWithoutDownloadingFullPlaylist() async throws {
        let url = "http://my-vionex.com:8080/tenant/get.php?username=fixture&password=fixture-only&type=m3u_plus&output=mpegts"
        let account = try Endpoint.loginAccount(mode: .m3u, server: url, allowingInsecureHTTP: true)
        XCTAssertEqual(account.mode, .xtream)
        XCTAssertEqual(account.server.absoluteString, "http://my-vionex.com:8080/tenant")
        XCTAssertEqual(account.username, "fixture")
        XCTAssertEqual(account.password, "fixture-only")
        XCTAssertTrue(account.insecureHTTPEnabled)
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [AccountImportProtocol.self]
        let session = URLSession(configuration: configuration)
        defer { session.invalidateAndCancel() }
        let expiry = try await APIClient(session: session).authenticate(account)
        XCTAssertEqual(expiry, "1800000000")
    }

    func testImportDecodesPHPQueryOnceAndRetainsEncodedTenantPath() throws {
        let account = try Endpoint.loginAccount(mode: .m3u, server: "https://my-vionex.com:8443/shared%2Ftenant/get.php?username=first+last%2Badmin&password=%252B%2B%26%3D%2F%C3%B1&type=m3u_plus")
        XCTAssertEqual(account.mode, .xtream)
        XCTAssertEqual(account.server.absoluteString, "https://my-vionex.com:8443/shared%2Ftenant")
        XCTAssertEqual(account.username, "first last+admin")
        XCTAssertEqual(account.password, "%2B+&=/ñ")
        let api = try XCTUnwrap(URLComponents(url: Endpoint.api(account), resolvingAgainstBaseURL: false))
        XCTAssertEqual(api.percentEncodedPath, "/shared%2Ftenant/player_api.php")
        XCTAssertEqual(api.queryItems?.first(where: { $0.name == "password" })?.value, account.password)
        XCTAssertFalse(api.percentEncodedQuery?.contains("+") ?? true)
        let manual = try Endpoint.loginAccount(mode: .xtream, server: account.server.absoluteString, username: account.username, password: account.password)
        XCTAssertEqual(account.storageID, manual.storageID)
    }

    func testImportStillRequiresConsentAndExactProviderHost() throws {
        for host in ["my-vionex.com", "moonspelltools.cc"] {
            let url = "http://\(host):8080/get.php?username=fixture&password=fixture-only&type=m3u"
            XCTAssertThrowsError(try Endpoint.loginAccount(mode: .m3u, server: url)) {
                XCTAssertEqual($0 as? PimflexError, .insecureURL)
            }
            XCTAssertEqual(try Endpoint.loginAccount(mode: .m3u, server: url, allowingInsecureHTTP: true).mode, .xtream)
        }
        XCTAssertThrowsError(try Endpoint.loginAccount(mode: .m3u, server: "http://sub.my-vionex.com/get.php?username=fixture&password=fixture-only&type=m3u", allowingInsecureHTTP: true))
        let deceptive = try Endpoint.loginAccount(mode: .m3u, server: "https://my-vionex.com.evil.example/get.php?username=fixture&password=fixture-only&type=m3u")
        XCTAssertEqual(deceptive.mode, .m3u)
    }

    func testGenericAndAmbiguousPlaylistLinksAreNotReinterpreted() throws {
        let urls = [
            "https://example.com/get.php?username=fixture&password=fixture-only&type=m3u_plus",
            "https://my-vionex.com/list.m3u?username=fixture&password=fixture-only&type=m3u_plus",
            "https://my-vionex.com/get.php?username=fixture&password=fixture-only&type=other",
            "https://my-vionex.com/get.php?username=fixture&username=other&password=fixture-only&type=m3u_plus",
            "https://my-vionex.com/get.php?username=fixture&password=fixture-only&type=m3u_plus&token=extra",
            "https://my-vionex.com/get.php?username=fixture&password=&type=m3u_plus"
        ]
        for url in urls {
            let account = try Endpoint.loginAccount(mode: .m3u, server: url)
            XCTAssertEqual(account.mode, .m3u)
            XCTAssertEqual(account.server.absoluteString, url)
        }
    }

    func testOversizedGenericPlaylistExplainsSizeWithoutChangingJSONLimit() async throws {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [AccountImportProtocol.self]
        let session = URLSession(configuration: configuration)
        defer { session.invalidateAndCancel() }
        let client = APIClient(session: session)
        let url = URL(string: "https://example.com/huge.m3u")!
        do {
            _ = try await client.playlist(Account(mode: .m3u, server: url))
            XCTFail("Oversized playlist must fail with actionable information")
        } catch { XCTAssertEqual(error as? PimflexError, .playlistTooLarge) }
        do {
            _ = try await client.data(from: url)
            XCTFail("The existing JSON resource limit must remain enforced")
        } catch { XCTAssertEqual(error as? PimflexError, .invalidResponse) }
    }
}

private final class AccountImportProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        guard let url = request.url else { return }
        let isAPI = url.path == "/tenant/player_api.php"
        let oversized = url.path == "/huge.m3u"
        let headers = oversized ? ["Content-Length": "33554433"] : ["Content-Type": "application/json"]
        let response = HTTPURLResponse(url: url, statusCode: isAPI || oversized ? 200 : 500, httpVersion: "HTTP/1.1", headerFields: headers)!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        let body = isAPI ? #"{"user_info":{"auth":1,"status":"Active","exp_date":"1800000000"}}"# : "#EXTM3U\n"
        client?.urlProtocol(self, didLoad: Data(body.utf8))
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() { }
}

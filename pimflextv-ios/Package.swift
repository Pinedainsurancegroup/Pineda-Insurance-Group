// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PimflexCore",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [.library(name: "PimflexCore", targets: ["PimflexCore"])],
    targets: [
        .target(name: "PimflexCore"),
        .testTarget(name: "PimflexCoreTests", dependencies: ["PimflexCore"])
    ]
)

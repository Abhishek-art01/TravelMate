// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TravelMateApp",
    platforms: [
        .iOS(.v17),
    ],
    products: [
        .library(
            name: "TravelMateApp",
            type: .dynamic,
            targets: ["TravelMateApp"]
        ),
    ],
    targets: [
        .target(
            name: "TravelMateApp",
            path: "Sources/TravelMateApp"
        ),
    ]
)

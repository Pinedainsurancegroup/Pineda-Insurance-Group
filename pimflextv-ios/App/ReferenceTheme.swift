import SwiftUI
import PimflexCore

enum ReferenceTheme {
    static let canvas = Color(red: 0.063, green: 0.047, blue: 0.18)
    static let panel = Color(red: 0.10, green: 0.12, blue: 0.23)
    static let accent = Color(red: 0.30, green: 0.72, blue: 0.90)
    static func font(_ size: CGFloat, bold: Bool = false) -> Font {
        .custom(bold ? "OpenSans-Bold" : "OpenSans", size: size, relativeTo: .body)
    }
}

struct ReferenceBackground: View {
    var login = false
    var body: some View {
        GeometryReader { proxy in
            Image(login ? "ReferenceLoginBackground" : "ReferenceBackground").resizable().scaledToFill()
                .frame(width: proxy.size.width, height: proxy.size.height).clipped()
        }.ignoresSafeArea().accessibilityHidden(true)
    }
}

struct Brand: View {
    var height: CGFloat = 74
    var body: some View {
        Image("ReferenceBrand").resizable().scaledToFit().frame(height: height)
            .accessibilityLabel("PIMFLEX TV")
    }
}

struct ReferenceButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.foregroundStyle(.white)
            .background {
                Image("ReferenceButton").resizable()
                    .opacity(configuration.isPressed ? 0.70 : 1)
            }
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
    }
}

struct DashboardTile: View {
    let title: String
    let artwork: String
    let height: CGFloat
    var updated: Date?
    private var cardImage: String {
        switch artwork { case "ReferenceLive": return "ReferenceLiveCard"; case "ReferenceMovies": return "ReferenceMoviesCard"; default: return "ReferenceSeriesCard" }
    }
    var body: some View {
        VStack(spacing: 0) {
            Text(title).font(ReferenceTheme.font(height > 170 ? 20 : 16, bold: true))
                .multilineTextAlignment(.center).minimumScaleFactor(0.75).padding(.top, 10)
            Spacer(minLength: 0)
            HStack(spacing: 6) {
                Text(updated.map { "Actualizado \($0.formatted(date: .omitted, time: .shortened))" } ?? "Abrir catálogo")
                    .font(.system(size: 10)).lineLimit(1)
                Image(systemName: "arrow.clockwise").font(.system(size: 10))
            }.padding(.vertical, 7).frame(maxWidth: .infinity).background(.black.opacity(0.10))
        }.frame(maxWidth: .infinity).frame(height: height).foregroundStyle(.white)
            .background { Image(cardImage).resizable() }
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .contentShape(RoundedRectangle(cornerRadius: 12))
    }
}

struct ReferenceShortcut: View {
    let title: String
    let artwork: String
    var unavailable = false
    var body: some View {
        VStack(spacing: 1) {
            Text(title).font(ReferenceTheme.font(11, bold: true)).lineLimit(2).minimumScaleFactor(0.8)
            if unavailable { Text("No disponible").font(.system(size: 9)) }
        }.padding(.leading, 22).padding(.trailing, 5).frame(maxWidth: .infinity).frame(height: 54)
            .foregroundStyle(.white).background { Image(artwork).resizable() }
    }
}

struct ShortcutLabel: View {
    let title: String
    let systemImage: String
    var compact = false
    var body: some View {
        VStack(spacing: compact ? 4 : 8) {
            Image(systemName: systemImage).font(.system(size: compact ? 18 : 25, weight: .medium))
                .accessibilityHidden(true)
            Text(title).font(ReferenceTheme.font(compact ? 10 : 12, bold: true)).multilineTextAlignment(.center)
        }.foregroundStyle(.white).frame(maxWidth: .infinity).frame(minHeight: compact ? 52 : 76)
            .padding(.horizontal, 5)
            .background(.black.opacity(0.24), in: RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(.white.opacity(0.2), lineWidth: 1))
    }
}

extension MediaKind {
    var referenceTitle: String {
        switch self { case .live: return "TV EN DIRECTO"; case .movie: return "CINE"; case .series: return "SERIES" }
    }
}

import SwiftUI

struct LicensesView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("PIMFLEX TV utiliza MobileVLCKit 3.7.5 de VideoLAN para reproducir formatos adicionales. MobileVLCKit se distribuye bajo GNU LGPL 2.1.")
                Link("Código fuente de MobileVLCKit", destination: URL(string: "https://code.videolan.org/videolan/VLCKit/-/tree/a213fd11")!)
                Link("Código fuente de libVLC", destination: URL(string: "https://code.videolan.org/videolan/vlc/-/tree/6de05adc")!)
                Text(license).font(.caption).textSelection(.enabled)
            }.padding()
        }.navigationTitle("Licencias").navigationBarTitleDisplayMode(.inline)
    }
    private var license: String {
        guard let url = Bundle.main.url(forResource: "MobileVLCKit-LICENSE", withExtension: "txt"),
              let text = try? String(contentsOf: url, encoding: .utf8) else { return "GNU Lesser General Public License, versión 2.1." }
        return text
    }
}

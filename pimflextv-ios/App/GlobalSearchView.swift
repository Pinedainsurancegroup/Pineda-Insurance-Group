import SwiftUI
import PimflexCore

struct GlobalSearchView: View {
    @EnvironmentObject private var model: AppModel
    @State private var query = ""
    @State private var items: [MediaItem] = []
    @State private var loading = true
    @State private var error: String?
    @State private var playback: MediaItem?
    private var matches: [MediaItem] {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return [] }
        return items.filter { $0.name.localizedCaseInsensitiveContains(query) }
    }
    var body: some View {
        Group {
            if loading { ProgressView("Cargando catálogos…") }
            else if query.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "magnifyingglass").font(.largeTitle)
                    Text("Busca en TV en directo, Cine y Series").multilineTextAlignment(.center)
                    if let error { Text(error).font(.footnote).foregroundStyle(.orange) }
                }.padding(32)
            } else if matches.isEmpty {
                VStack(spacing: 16) {
                    Text("No se encontraron resultados")
                    if let error { Text(error).font(.footnote).foregroundStyle(.orange) }
                }.padding()
            } else {
                List {
                    if let error { Text(error).font(.footnote).foregroundStyle(.orange) }
                    ForEach(MediaKind.allCases) { kind in
                        let results = matches.filter { $0.kind == kind }
                        if !results.isEmpty {
                            Section(kind.referenceTitle) {
                                ForEach(results) { item in
                                    if kind == .series {
                                        NavigationLink { SeriesView(series: item) } label: { MediaRow(item: item) }
                                    } else {
                                        Button { playback = item } label: { MediaRow(item: item) }.buttonStyle(.plain)
                                    }
                                }.listRowBackground(ReferenceTheme.panel)
                            }
                        }
                    }
                }.listStyle(.plain).scrollContentBackground(.hidden)
            }
        }.frame(maxWidth: .infinity, maxHeight: .infinity).background { ReferenceBackground() }
            .navigationTitle("Búsqueda maestra").navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar)
            .searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always), prompt: "Buscar en todos los catálogos")
            .fullScreenCover(item: $playback) { PlayerScreen(item: $0) }
            .task {
                defer { loading = false }
                let account = model.account
                var collected: [MediaItem] = []
                var failed = false
                for kind in MediaKind.allCases {
                    do { collected.append(contentsOf: (try await model.catalog(kind)).1) }
                    catch is CancellationError { return }
                    catch { failed = true }
                }
                guard model.account == account else { return }
                items = collected
                if failed { error = "No se pudieron cargar todos los catálogos. Vuelve a intentar desde el inicio." }
            }
    }
}

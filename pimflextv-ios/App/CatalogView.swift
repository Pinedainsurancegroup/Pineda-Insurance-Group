import SwiftUI
import PimflexCore

struct CatalogView: View {
    @EnvironmentObject private var model: AppModel
    let kind: MediaKind
    @State private var categories: [PimflexCore.Category] = []
    @State private var items: [MediaItem] = []
    @State private var category = ""
    @State private var search = ""
    @State private var favoriteOnly = false
    @State private var loading = false
    @State private var error: String?
    @State private var playback: MediaItem?
    @State private var guide: MediaItem?
    private var displayed: [MediaItem] {
        items.filter { (category.isEmpty || $0.categoryID == category) &&
            (!favoriteOnly || model.favorites.contains($0.id)) &&
            (search.isEmpty || $0.name.localizedCaseInsensitiveContains(search)) }
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Picker("Categoría", selection: $category) {
                    Text("Todas las categorías").tag("")
                    ForEach(categories) { Text($0.name).tag($0.id) }
                }.lineLimit(1)
                Spacer()
                Toggle(isOn: $favoriteOnly) { Image(systemName: "star.fill") }
                    .toggleStyle(.button).accessibilityLabel("Solo favoritos")
            }.padding(.horizontal)
            if loading { ProgressView("Cargando catálogo…").padding(); Spacer() }
            else if let error {
                VStack(spacing: 16) { Text(error); Button("Reintentar") { Task { await load() } } }.padding(); Spacer()
            } else if displayed.isEmpty {
                VStack(spacing: 14) {
                    Image(systemName: "rectangle.stack").font(.largeTitle)
                    Text("No hay títulos para mostrar").font(.headline)
                    Text(kind == .series && model.account?.mode == .m3u ? "Las temporadas y episodios requieren acceso por usuario y contraseña." : "Prueba otra categoría o búsqueda.")
                        .foregroundStyle(.secondary)
                }.padding(32); Spacer()
            } else {
                List(displayed) { item in
                    HStack(spacing: 12) {
                        if kind == .series {
                            NavigationLink { SeriesView(series: item) } label: { MediaRow(item: item) }
                        } else {
                            Button { playback = item } label: { MediaRow(item: item) }.buttonStyle(.plain)
                        }
                        if kind == .live && model.account?.mode == .xtream {
                            Button { guide = item } label: { Image(systemName: "list.bullet.rectangle") }
                                .buttonStyle(.borderless).accessibilityLabel("Programación de \(item.name)")
                        }
                        Button { model.toggleFavorite(item) } label: {
                            Image(systemName: model.favorites.contains(item.id) ? "star.fill" : "star")
                        }.buttonStyle(.borderless).accessibilityLabel("Favorito: \(item.name)")
                    }.listRowBackground(Color.white.opacity(0.04))
                }.listStyle(.plain).refreshable { await load() }
            }
        }.navigationTitle(kind.title).searchable(text: $search, prompt: "Buscar en este catálogo")
            .task { await load() }
            .fullScreenCover(item: $playback) { PlayerScreen(item: $0) }
            .sheet(item: $guide) { GuideView(item: $0) }
    }
    @MainActor private func load() async {
        guard let account = model.account else { return }
        loading = true; error = nil
        defer { loading = false }
        do {
            if account.mode == .m3u {
                let entries = try await model.api.playlist(account)
                items = entries.filter { $0.kind == kind }
                categories = Set(items.map(\.categoryID)).filter { !$0.isEmpty }.sorted().map { PimflexCore.Category(id: $0, name: $0) }
            } else {
                async let groups = model.api.categories(account, kind: kind)
                async let catalog = model.api.catalog(account, kind: kind)
                (categories, items) = try await (groups, catalog)
            }
            if !categories.contains(where: { $0.id == category }) { category = "" }
        } catch is CancellationError { }
        catch { self.error = model.message(error) }
    }
}

struct MediaRow: View {
    let item: MediaItem
    var body: some View {
        HStack(spacing: 14) {
            AsyncImage(url: item.artwork) { image in image.resizable().scaledToFit() } placeholder: {
                Image(systemName: item.kind == .live ? "tv" : "film").font(.title2).foregroundStyle(.cyan)
            }.frame(width: 58, height: 68).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 8))
            VStack(alignment: .leading, spacing: 6) {
                Text(item.name).font(.headline).foregroundStyle(.primary).lineLimit(2)
                if let season = item.season { Text("Temporada \(season) · Episodio \(item.episode ?? 0)").font(.caption).foregroundStyle(.secondary) }
                else { Text(item.kind.title).font(.caption).foregroundStyle(.secondary) }
            }
            Spacer(minLength: 0)
        }.padding(.vertical, 5).contentShape(Rectangle())
    }
}

struct SeriesView: View {
    @EnvironmentObject private var model: AppModel
    let series: MediaItem
    @State private var episodes: [MediaItem] = []
    @State private var loading = true
    @State private var error: String?
    @State private var playback: MediaItem?
    var body: some View {
        Group {
            if loading { ProgressView("Cargando episodios…") }
            else if let error { VStack { Text(error); Button("Reintentar") { Task { await load() } } }.padding() }
            else if episodes.isEmpty { Text("El proveedor no devolvió episodios.") }
            else {
                List {
                    ForEach(Set(episodes.map { $0.season ?? 0 }).sorted(), id: \.self) { season in
                        Section("Temporada \(season)") {
                            ForEach(episodes.filter { ($0.season ?? 0) == season }) { item in
                                Button { playback = item } label: { MediaRow(item: item) }.buttonStyle(.plain)
                            }
                        }
                    }
                }
            }
        }.navigationTitle(series.name).task { await load() }
            .fullScreenCover(item: $playback) { PlayerScreen(item: $0) }
    }
    @MainActor private func load() async {
        guard let account = model.account else { return }
        loading = true; error = nil; defer { loading = false }
        do { episodes = try await model.api.episodes(account, seriesID: series.providerID) }
        catch is CancellationError { }
        catch { self.error = model.message(error) }
    }
}

struct GuideView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    let item: MediaItem
    @State private var programmes: [Programme] = []
    @State private var loading = true
    @State private var error: String?
    var body: some View {
        NavigationStack {
            Group {
                if loading { ProgressView("Cargando guía…") }
                else if let error { Text(error).padding() }
                else if programmes.isEmpty { Text("Sin programación disponible para este canal.").padding() }
                else {
                    List(programmes) { programme in
                        VStack(alignment: .leading, spacing: 8) {
                            if let date = programme.start { Text(date.formatted(date: .abbreviated, time: .shortened)).font(.caption).foregroundStyle(.cyan) }
                            Text(programme.title).font(.headline)
                            Text(programme.description).font(.callout).foregroundStyle(.secondary)
                        }.padding(.vertical, 6)
                    }
                }
            }.navigationTitle(item.name).toolbar { Button("Cerrar") { dismiss() } }
                .task {
                    defer { loading = false }
                    guard let account = model.account else { return }
                    do { programmes = try await model.api.guide(account, streamID: item.providerID) }
                    catch is CancellationError { }
                    catch { self.error = model.message(error) }
                }
        }
    }
}

import SwiftUI
import PimflexCore

struct CatalogView: View {
    @EnvironmentObject private var model: AppModel
    let kind: MediaKind
    let guideMode: Bool
    @State private var categories: [PimflexCore.Category] = []
    @State private var items: [MediaItem] = []
    @State private var category = ""
    @State private var search = ""
    @State private var favoriteOnly: Bool
    @State private var loading = false
    @State private var error: String?
    @State private var playback: MediaItem?
    @State private var guide: MediaItem?

    init(kind: MediaKind, guideMode: Bool = false, favoritesOnly: Bool = false) {
        self.kind = kind; self.guideMode = guideMode
        _favoriteOnly = State(initialValue: favoritesOnly)
    }
    private var displayed: [MediaItem] {
        items.filter { (category.isEmpty || $0.categoryID == category) &&
            (!favoriteOnly || model.favorites.contains($0.id)) &&
            (search.isEmpty || $0.name.localizedCaseInsensitiveContains(search)) }
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass").foregroundStyle(.white.opacity(0.65))
                TextField("Buscar en este catálogo", text: $search).accessibilityIdentifier("catalogSearch")
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                if !search.isEmpty {
                    Button { search = "" } label: { Image(systemName: "xmark.circle.fill") }.accessibilityLabel("Borrar búsqueda")
                }
            }.padding(13).background(.black.opacity(0.3), in: RoundedRectangle(cornerRadius: 10))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(.white.opacity(0.25), lineWidth: 1)).padding(.horizontal)
            HStack {
                Picker("Categoría", selection: $category) {
                    Text("Todas las categorías").tag("")
                    ForEach(categories) { Text($0.name).tag($0.id) }
                }.lineLimit(1).accessibilityIdentifier("categoryPicker")
                Spacer()
                Button { favoriteOnly.toggle() } label: {
                    Image(systemName: favoriteOnly ? "star.fill" : "star")
                        .frame(width: 44, height: 44)
                }.accessibilityLabel(favoriteOnly ? "Mostrar todos" : "Solo favoritos")
                    .accessibilityIdentifier("favoriteFilter")
            }.padding(.horizontal)
            content
        }.background { ReferenceBackground() }
            .navigationTitle(guideMode ? "GUÍA DE TV" : kind.referenceTitle).navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar)
            .task { await load() }
            .fullScreenCover(item: $playback) { PlayerScreen(item: $0) }
            .sheet(item: $guide) { GuideView(item: $0) }
    }
    @ViewBuilder private var content: some View {
        if loading { ProgressView("Cargando catálogo…").padding(); Spacer() }
        else if let error {
            VStack(spacing: 16) { Text(error); Button("Reintentar") { Task { await load(refresh: true) } } }.padding(); Spacer()
        } else if displayed.isEmpty {
            VStack(spacing: 14) {
                Image(systemName: favoriteOnly ? "star" : "rectangle.stack").font(.largeTitle)
                Text(favoriteOnly ? "Todavía no hay favoritos" : "No hay títulos para mostrar").font(.headline)
                Text(kind == .series && model.account?.mode == .m3u ? "Las temporadas y episodios requieren acceso por usuario y contraseña." : favoriteOnly ? "Toca la estrella de un título para guardarlo aquí." : "Prueba otra categoría o búsqueda.")
                    .foregroundStyle(.secondary)
            }.multilineTextAlignment(.center).padding(32); Spacer()
        } else if kind == .live {
            List(displayed) { item in
                HStack(spacing: 12) {
                    Button { if guideMode { guide = item } else { playback = item } } label: { MediaRow(item: item) }
                        .buttonStyle(.plain).accessibilityIdentifier("channel-\(item.id)")
                    if !guideMode && model.account?.mode == .xtream {
                        Button { guide = item } label: { Image(systemName: "list.bullet.rectangle").frame(width: 36, height: 44) }
                            .buttonStyle(.borderless).accessibilityLabel("Programación de \(item.name)")
                    }
                    favoriteButton(item)
                }.listRowBackground(ReferenceTheme.panel.opacity(0.88))
            }.listStyle(.plain).scrollContentBackground(.hidden).refreshable { await load(refresh: true) }
        } else {
            ScrollView {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 140, maximum: 220), spacing: 16)], spacing: 18) {
                    ForEach(displayed) { item in
                        VStack(spacing: 0) {
                            if kind == .series {
                                NavigationLink { SeriesView(series: item) } label: { PosterView(item: item) }
                                    .buttonStyle(.plain).accessibilityIdentifier("series-\(item.id)")
                            } else {
                                Button { playback = item } label: { PosterView(item: item) }
                                    .buttonStyle(.plain).accessibilityIdentifier("movie-\(item.id)")
                            }
                            HStack {
                                Text(item.name).font(ReferenceTheme.font(13, bold: true)).lineLimit(2).frame(maxWidth: .infinity, alignment: .leading)
                                favoriteButton(item)
                            }.padding(.leading, 10).frame(minHeight: 57)
                        }.background(ReferenceTheme.panel.opacity(0.94), in: RoundedRectangle(cornerRadius: 12))
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                }.padding(.horizontal, 16).padding(.bottom, 24)
            }.refreshable { await load(refresh: true) }
        }
    }
    private func favoriteButton(_ item: MediaItem) -> some View {
        Button { model.toggleFavorite(item) } label: {
            Image(systemName: model.favorites.contains(item.id) ? "star.fill" : "star")
                .foregroundStyle(model.favorites.contains(item.id) ? .yellow : .white.opacity(0.8))
                .frame(width: 44, height: 44)
        }.buttonStyle(.borderless).accessibilityLabel("Favorito: \(item.name)")
            .accessibilityIdentifier("favorite-\(item.id)")
    }
    @MainActor private func load(refresh: Bool = false) async {
        guard model.account != nil else { return }
        loading = true; error = nil
        defer { loading = false }
        do {
            (categories, items) = try await model.catalog(kind, refresh: refresh)
            if !categories.contains(where: { $0.id == category }) { category = "" }
        } catch is CancellationError { }
        catch { self.error = model.message(error) }
    }
}

struct PosterView: View {
    let item: MediaItem
    var body: some View {
        ZStack {
            Rectangle().fill(LinearGradient(colors: [.indigo.opacity(0.6), ReferenceTheme.panel], startPoint: .topLeading, endPoint: .bottomTrailing))
            AsyncImage(url: item.artwork) { image in
                image.resizable().scaledToFill()
            } placeholder: {
                VStack(spacing: 14) {
                    Image(item.kind == .series ? "ReferenceSeries" : "ReferenceMovies")
                        .resizable().scaledToFit().frame(width: 55, height: 55)
                    Text(item.kind.referenceTitle).font(ReferenceTheme.font(11, bold: true))
                }.foregroundStyle(.white.opacity(0.65))
            }
        }.frame(height: 190).clipped().accessibilityLabel(item.name)
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
        }.navigationTitle(series.name).navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar).task { await load() }
            .fullScreenCover(item: $playback) { PlayerScreen(item: $0) }
    }
    @MainActor private func load() async {
        guard let account = model.account else { return }
        loading = true; error = nil; defer { loading = false }
        do {
            #if DEBUG
            if model.usesTestFixtures {
                episodes = (1...3).map { MediaItem(providerID: String($0), name: "Episodio de muestra \($0)", kind: .series, season: 1, episode: $0) }
                return
            }
            #endif
            episodes = try await model.api.episodes(account, seriesID: series.providerID)
        }
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
                    guard account.mode == .xtream else {
                        error = "La guía de programación requiere acceso por usuario y contraseña. Esta lista M3U no incluye una guía compatible."
                        return
                    }
                    do { if !model.usesTestFixtures { programmes = try await model.api.guide(account, streamID: item.providerID) } }
                    catch is CancellationError { }
                    catch { self.error = model.message(error) }
                }
        }
    }
}

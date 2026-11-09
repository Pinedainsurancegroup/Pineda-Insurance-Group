import SwiftUI
import PimflexCore

@main
struct PimflexApp: App {
    @StateObject private var model = AppModel()
    var body: some Scene {
        WindowGroup {
            Group {
                if model.account != nil { MainView().id(model.account?.storageID) }
                else { LoginView() }
            }
            .modifier(TestWindowWidth())
            .environmentObject(model)
            .tint(ReferenceTheme.accent)
            .preferredColorScheme(.dark)
        }
    }
}

// A deterministic narrow content window for UI regression tests. Release builds
// never read this environment variable; this does not simulate OS multitasking.
private struct TestWindowWidth: ViewModifier {
    func body(content: Content) -> some View {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing"),
           let raw = ProcessInfo.processInfo.environment["PIMFLEX_TEST_CONTENT_WIDTH"],
           let width = Double(raw), width.isFinite, width >= 320, width <= 600 {
            content.frame(maxWidth: CGFloat(width)).frame(maxWidth: .infinity)
        } else { content }
        #else
        content
        #endif
    }
}

struct LoginView: View {
    @EnvironmentObject private var model: AppModel
    @State private var mode: SourceMode = .xtream
    @State private var server = ""
    @State private var username = ""
    @State private var password = ""
    @State private var showPassword = false
    @State private var allowingInsecureHTTP = false
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    private var compact: Bool { verticalSizeClass == .compact }
    @FocusState private var focusedField: LoginField?
    private enum LoginField: Hashable { case server, username, password }

    var body: some View {
        NavigationStack {
            GeometryReader { geometry in
                ScrollView {
                    VStack(spacing: compact ? 10 : 22) {
                        Brand(height: compact ? 44 : 90).padding(.top, compact ? 0 : 20)
                        Text("DETALLES DE ACCESO").font(ReferenceTheme.font(compact ? 18 : 22, bold: true))
                        Picker("Tipo de acceso", selection: $mode) {
                            Text("Usuario y contraseña").tag(SourceMode.xtream)
                            Text("Lista M3U").tag(SourceMode.m3u)
                        }.pickerStyle(.segmented).accessibilityIdentifier("sourceMode")
                        VStack(spacing: compact ? 8 : 14) {
                            loginField(icon: "globe") {
                                TextField(mode == .xtream ? "URL del servidor (https://…)" : "URL HTTPS de la lista M3U", text: $server)
                                    .keyboardType(.URL).textContentType(.URL).submitLabel(.next)
                                    .focused($focusedField, equals: .server).accessibilityIdentifier("serverField")
                            }
                            if mode == .xtream {
                                loginField(icon: "person.fill") {
                                    TextField("Usuario", text: $username).textContentType(.username)
                                        .submitLabel(.next).focused($focusedField, equals: .username)
                                        .accessibilityIdentifier("usernameField")
                                }
                                loginField(icon: "lock.fill") {
                                    Group {
                                        if showPassword { TextField("Contraseña", text: $password) }
                                        else { SecureField("Contraseña", text: $password) }
                                    }.textContentType(.password).submitLabel(.go)
                                        .focused($focusedField, equals: .password)
                                        .accessibilityIdentifier("passwordField")
                                    Button { showPassword.toggle() } label: {
                                        Image(systemName: showPassword ? "eye.slash" : "eye")
                                            .frame(width: 32, height: 32)
                                    }.accessibilityLabel(showPassword ? "Ocultar contraseña" : "Mostrar contraseña")
                                }
                            }
                        }.textInputAutocapitalization(.never).autocorrectionDisabled()
                        if server.trimmingCharacters(in: .whitespacesAndNewlines).lowercased().hasPrefix("http://") {
                            VStack(alignment: .leading, spacing: 6) {
                                Toggle("Mi servidor requiere HTTP", isOn: $allowingInsecureHTTP)
                                    .font(.callout).accessibilityIdentifier("httpOptIn")
                                Text("HTTP envía tus datos sin cifrar. Activa esta opción sólo si tu proveedor te dio una dirección HTTP; usa HTTPS cuando esté disponible.")
                                    .font(.caption).foregroundStyle(.white.opacity(0.8))
                            }
                        }
                        if let error = model.error {
                            Text(error).font(.callout).foregroundStyle(.white)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(12).background(.red.opacity(0.38), in: RoundedRectangle(cornerRadius: 8))
                                .accessibilityIdentifier("loginError")
                        }
                        Button(action: connect) {
                            HStack(spacing: 12) {
                                if model.connecting { ProgressView().tint(.white) }
                                Text(model.connecting ? "CONECTANDO…" : "INICIAR SESIÓN")
                                    .font(ReferenceTheme.font(17, bold: true))
                            }.frame(maxWidth: .infinity).frame(height: compact ? 44 : 56)
                        }.buttonStyle(ReferenceButtonStyle()).disabled(model.connecting || server.isEmpty)
                            .opacity(server.isEmpty ? 0.65 : 1).accessibilityIdentifier("connectButton")
                        NavigationLink { SavedAccountsView() } label: {
                            Label("LISTA DE USUARIOS", systemImage: "person.2.fill")
                                .font(ReferenceTheme.font(12, bold: true)).frame(maxWidth: .infinity).frame(height: 38)
                                .background(.black.opacity(0.2), in: RoundedRectangle(cornerRadius: 8))
                        }.accessibilityIdentifier("savedAccountsButton")
                        if !compact {
                            Text("Ingresa los datos de tu cuenta PIMFLEX TV.")
                                .font(.footnote).foregroundStyle(.white.opacity(0.8))
                        }
                    }.padding(compact ? 14 : 26).frame(maxWidth: compact ? 440 : 520)
                        .background { Image("ReferenceLoginPanel").resizable() }
                        .padding(compact ? 10 : 20)
                        .frame(maxWidth: .infinity, minHeight: geometry.size.height)
                }.scrollDismissesKeyboard(.interactively)
            }.background { ReferenceBackground(login: true) }
                .onSubmit {
                    switch focusedField {
                    case .server: if mode == .xtream { focusedField = .username } else { connect() }
                    case .username: focusedField = .password
                    default: connect()
                    }
                }
        }
    }
    private func loginField<Content: View>(icon: String, @ViewBuilder content: () -> Content) -> some View {
        HStack(spacing: 14) {
            Image(systemName: icon).frame(width: 24).foregroundStyle(.white.opacity(0.85)).accessibilityHidden(true)
            content()
        }.font(ReferenceTheme.font(16)).padding(.horizontal, 16).frame(minHeight: compact ? 44 : 54)
            .background { Image("ReferenceLoginField").resizable() }
    }
    private func connect() {
        guard !model.connecting, !server.isEmpty else { return }
        focusedField = nil
        Task {
            await model.connect(mode: mode, server: server, username: username, password: password, allowingInsecureHTTP: allowingInsecureHTTP)
            if model.account != nil { password = "" }
        }
    }
}

struct MainView: View {
    var body: some View {
        NavigationStack { HomeView() }
    }
}

struct HomeView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dynamicTypeSize) private var textSize
    @State private var confirmSignOut = false
    @State private var refreshing = false
    var body: some View {
        GeometryReader { geometry in
            let wide = geometry.size.width > 650 && !textSize.isAccessibilitySize
            let referenceCardHeightRatio: CGFloat = 451.0 / 509.0
            let sidebarWidth = min(120.0, geometry.size.width * 0.14)
            let landscapeContentWidth = min(1100.0, geometry.size.width - sidebarWidth - 12.0)
            let landscapeCardHeight = max(1.0, (landscapeContentWidth - 14.0 - 32.0) / 3.0) * referenceCardHeightRatio
            let portraitCardWidth = max(1.0, min(1100.0, geometry.size.width) - 32.0)
            HStack(spacing: 12) {
                if wide { sidebar.frame(width: sidebarWidth) }
                ScrollView {
                    VStack(spacing: wide ? 14 : 20) {
                        header(wide: wide)
                        if wide {
                            HStack(spacing: 16) {
                                mediaTile(.live, height: landscapeCardHeight)
                                mediaTile(.movie, height: landscapeCardHeight)
                                mediaTile(.series, height: landscapeCardHeight)
                            }
                        } else {
                            mediaTile(.live, height: portraitCardWidth * referenceCardHeightRatio)
                            HStack(spacing: 16) {
                                mediaTile(.movie, height: (portraitCardWidth - 16) / 2 * referenceCardHeightRatio)
                                mediaTile(.series, height: (portraitCardWidth - 16) / 2 * referenceCardHeightRatio)
                            }
                        }
                        HStack(spacing: 14) {
                            ReferenceShortcut(title: "CATCH UP", artwork: "ReferenceCatchup", unavailable: true)
                                .opacity(0.55).accessibilityLabel("Catch up, todavía no disponible")
                            NavigationLink { MultiScreenView() } label: {
                                ReferenceShortcut(title: "PANTALLA MULTIPLE", artwork: "ReferenceMultiscreen")
                            }.accessibilityIdentifier("multiScreenShortcut")
                            NavigationLink { CatalogView(kind: .live, guideMode: true) } label: {
                                ReferenceShortcut(title: "EPG", artwork: "ReferenceEPG")
                            }.accessibilityIdentifier("guideShortcut")
                        }.buttonStyle(.plain)
                        if let error = model.error {
                            Text(error).font(.callout).foregroundStyle(.white).padding(10)
                                .frame(maxWidth: .infinity).background(.red.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
                        }
                        footer
                    }.padding(.vertical, wide ? 10 : 16).padding(.trailing, wide ? 14 : 16)
                        .padding(.leading, wide ? 0 : 16).frame(maxWidth: 1100).frame(maxWidth: .infinity)
                }
            }.background { ReferenceBackground() }
        }.toolbar(.hidden, for: .navigationBar).task { await model.restore() }
            .confirmationDialog("¿Cerrar la sesión de PIMFLEX TV?", isPresented: $confirmSignOut, titleVisibility: .visible) {
                Button("Cerrar sesión", role: .destructive) { model.signOut() }
            }
    }
    private var sidebar: some View {
        VStack(spacing: 12) {
            Brand(height: 43).padding(.top, 8)
            Spacer(minLength: 0)
            NavigationLink { AccountInfoView() } label: {
                sidebarIcon("ReferenceSidebarAccount", label: "Mi Información")
            }.accessibilityLabel("Mi Información")
            NavigationLink { SettingsView() } label: {
                sidebarIcon("ReferenceSidebarSettings", label: "Ajustes")
            }.accessibilityLabel("Ajustes").accessibilityIdentifier("settingsButton")
            NavigationLink { SavedAccountsView() } label: {
                sidebarIcon("ReferenceSidebarUsers", label: "Lista de Usuarios")
            }.accessibilityLabel("Lista de Usuarios").accessibilityIdentifier("savedAccountsButton")
            Menu {
                NavigationLink { FavoritesView() } label: { Label("Favoritos", systemImage: "star.fill") }
                Button { refresh() } label: { Label("Actualizar catálogos", systemImage: "arrow.clockwise") }
                Button("Cerrar sesión", role: .destructive) { confirmSignOut = true }
            } label: {
                Image(systemName: "ellipsis").font(.title2).frame(width: 54, height: 40)
            }.accessibilityLabel("Más opciones")
            Spacer(minLength: 0)
        }.foregroundStyle(.white)
    }
    private func sidebarIcon(_ image: String, label: String) -> some View {
        Image(image).resizable().scaledToFit().frame(width: 30, height: 30)
            .frame(width: 54, height: 44).accessibilityLabel(label)
    }
    private func header(wide: Bool) -> some View {
        HStack(spacing: 12) {
            if !wide { Brand(height: 40).frame(maxWidth: 150, alignment: .leading) }
            Spacer(minLength: 0)
            if wide {
                TimelineView(.periodic(from: .now, by: 60)) { context in
                    Text(context.date.formatted(date: .abbreviated, time: .shortened))
                        .font(ReferenceTheme.font(12)).foregroundStyle(.white.opacity(0.85))
                }
            }
            NavigationLink { GlobalSearchView() } label: {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                    if wide { Text("Búsqueda maestra").font(ReferenceTheme.font(11)) }
                }.padding(.horizontal, 14).frame(height: 38)
                    .background { if wide { Image("ReferenceSearch").resizable() } }
            }.accessibilityLabel("Búsqueda maestra").accessibilityIdentifier("globalSearchButton")
            if !wide {
                NavigationLink { SettingsView() } label: {
                    Image(systemName: "gearshape").font(.title2).frame(width: 44, height: 44)
                }.accessibilityLabel("Ajustes").accessibilityIdentifier("settingsButton")
            }
        }.foregroundStyle(.white)
    }
    private func mediaTile(_ kind: MediaKind, height: CGFloat) -> some View {
        NavigationLink { CatalogView(kind: kind) } label: {
            DashboardTile(title: kind.referenceTitle, artwork: kind == .live ? "ReferenceLive" : kind == .movie ? "ReferenceMovies" : "ReferenceSeries", height: height, updated: model.lastUpdated[kind])
        }.buttonStyle(.plain).accessibilityIdentifier("dashboard-\(kind.rawValue)")
    }
    private var footer: some View {
        HStack(spacing: 12) {
            Label((model.account?.username.isEmpty == false ? model.account?.username : nil) ?? "Lista M3U", systemImage: "person.circle")
            Spacer()
            if refreshing { ProgressView().scaleEffect(0.7) }
            if let seconds = Double(model.expiration), seconds.isFinite, seconds > 0 {
                Text("Vence: \(Date(timeIntervalSince1970: seconds).formatted(date: .abbreviated, time: .omitted))")
            }
        }.font(ReferenceTheme.font(11)).foregroundStyle(.white.opacity(0.85))
    }
    private func refresh() {
        guard !refreshing else { return }
        Task { refreshing = true; await model.refreshCatalogs(); refreshing = false }
    }
}

struct FavoritesView: View {
    @State private var kind: MediaKind = .live
    var body: some View {
        VStack(spacing: 0) {
            Picker("Catálogo", selection: $kind) {
                ForEach(MediaKind.allCases) { Text($0.title).tag($0) }
            }.pickerStyle(.segmented).padding()
            CatalogView(kind: kind, favoritesOnly: true).id(kind)
        }.background { ReferenceBackground() }.navigationTitle("Favoritos")
    }
}

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel
    @State private var confirmReset = false
    @State private var confirmSignOut = false
    var body: some View {
        Form {
            Section {
                Brand(height: 58).frame(maxWidth: .infinity).padding(.vertical, 12)
            }.listRowBackground(Color.clear)
            Section {
                NavigationLink("Lista de Usuarios") { SavedAccountsView() }.accessibilityIdentifier("savedAccountsButton")
                NavigationLink("Favoritos") { FavoritesView() }
            }
            Section("Mi cuenta") {
                if let account = model.account {
                    LabeledContent("Usuario", value: account.username.isEmpty ? "Lista M3U" : account.username)
                    LabeledContent("Servidor", value: account.server.host ?? "")
                    LabeledContent("Acceso", value: account.mode == .xtream ? "Usuario y contraseña" : "Lista M3U")
                }
                if let seconds = Double(model.expiration), seconds.isFinite, seconds > 0 {
                    LabeledContent("Vencimiento", value: Date(timeIntervalSince1970: seconds).formatted(date: .abbreviated, time: .omitted))
                }
                Button("Actualizar cuenta") { Task { await model.restore() } }
                if let error = model.error { Text(error).foregroundStyle(.orange) }
            }
            Section("Reproducción") {
                Label("Audio, subtítulos y AirPlay en el reproductor", systemImage: "play.rectangle")
                    .font(.callout)
                Text("La disponibilidad de pistas y formatos depende de la transmisión.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Mis datos") {
                Button("Borrar favoritos e historial", role: .destructive) { confirmReset = true }
            }
            Section("Acerca de") {
                LabeledContent("Aplicación", value: "PIMFLEX TV")
                LabeledContent("Versión", value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0.2.0")
            }
            Section { Button("Cerrar sesión", role: .destructive) { confirmSignOut = true } }
        }.scrollContentBackground(.hidden).background { ReferenceBackground() }
            .navigationTitle("AJUSTES").navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar)
            .confirmationDialog("¿Borrar tus favoritos y el historial de esta cuenta?", isPresented: $confirmReset, titleVisibility: .visible) {
                Button("Borrar", role: .destructive) { model.resetPreferences() }
            }
            .confirmationDialog("¿Cerrar la sesión de PIMFLEX TV?", isPresented: $confirmSignOut, titleVisibility: .visible) {
                Button("Cerrar sesión", role: .destructive) { model.signOut() }
            }
    }
}

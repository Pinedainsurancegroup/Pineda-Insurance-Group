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
            .environmentObject(model)
            .tint(.cyan)
            .preferredColorScheme(.dark)
        }
    }
}

struct Brand: View {
    var body: some View {
        Image("Brand").resizable().scaledToFit().frame(height: 80)
            .padding(.horizontal, 14).background(.white, in: RoundedRectangle(cornerRadius: 15))
            .accessibilityLabel("PIMFLEX TV")
    }
}

struct LoginView: View {
    @EnvironmentObject private var model: AppModel
    @State private var mode: SourceMode = .xtream
    @State private var server = ""
    @State private var username = ""
    @State private var password = ""
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Brand().frame(maxWidth: .infinity).padding(.top, 32)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Tu entretenimiento, contigo.").font(.largeTitle.bold())
                        Text("Conecta tu cuenta para ver TV, películas y series.").foregroundStyle(.secondary)
                    }
                    Picker("Tipo de acceso", selection: $mode) {
                        Text("Usuario y contraseña").tag(SourceMode.xtream)
                        Text("Lista M3U").tag(SourceMode.m3u)
                    }.pickerStyle(.segmented)
                    VStack(spacing: 16) {
                        TextField(mode == .xtream ? "Servidor https://…" : "URL HTTPS de la lista", text: $server)
                            .keyboardType(.URL).textContentType(.URL).accessibilityIdentifier("serverField")
                        if mode == .xtream {
                            TextField("Usuario", text: $username).textContentType(.username).accessibilityIdentifier("usernameField")
                            SecureField("Contraseña", text: $password).textContentType(.password).accessibilityIdentifier("passwordField")
                        }
                    }.textFieldStyle(.roundedBorder).textInputAutocapitalization(.never).autocorrectionDisabled()
                    if let error = model.error { Text(error).foregroundStyle(.orange).accessibilityIdentifier("loginError") }
                    Button {
                        Task { await model.connect(mode: mode, server: server, username: username, password: password); password = "" }
                    } label: {
                        HStack { Spacer(); if model.connecting { ProgressView() }; Text(model.connecting ? "Conectando…" : "Conectar").bold(); Spacer() }.padding(8)
                    }.buttonStyle(.borderedProminent).disabled(model.connecting || server.isEmpty)
                        .accessibilityIdentifier("connectButton")
                    Text("Usa los datos de tu proveedor. La app no incluye canales ni suscripciones.")
                        .font(.footnote).foregroundStyle(.secondary)
                }.padding(24).frame(maxWidth: 600).frame(maxWidth: .infinity)
            }.background(Color(red: 0.035, green: 0.05, blue: 0.11))
        }
    }
}

struct MainView: View {
    @EnvironmentObject private var model: AppModel
    var body: some View {
        TabView {
            NavigationStack { HomeView() }.tabItem { Label("Inicio", systemImage: "house.fill") }
            NavigationStack { CatalogView(kind: .live) }.tabItem { Label("TV", systemImage: "tv") }
            NavigationStack { CatalogView(kind: .movie) }.tabItem { Label("Películas", systemImage: "film") }
            NavigationStack { CatalogView(kind: .series) }.tabItem { Label("Series", systemImage: "play.rectangle.on.rectangle") }
            NavigationStack { SettingsView() }.tabItem { Label("Cuenta", systemImage: "person.crop.circle") }
        }.task { await model.restore() }
    }
}

struct HomeView: View {
    @EnvironmentObject private var model: AppModel
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Brand().frame(maxWidth: .infinity)
                Text("¿Qué quieres ver hoy?").font(.title.bold())
                ForEach(MediaKind.allCases) { kind in
                    NavigationLink { CatalogView(kind: kind) } label: {
                        HStack(spacing: 18) {
                            Image(systemName: kind == .live ? "tv.fill" : kind == .movie ? "film.fill" : "play.rectangle.on.rectangle.fill")
                                .font(.system(size: 32)).frame(width: 50)
                            VStack(alignment: .leading, spacing: 6) {
                                Text(kind.title).font(.title2.bold())
                                Text(kind == .live ? "Tus canales en directo" : "Explora el catálogo de tu cuenta").font(.caption)
                            }
                            Spacer(); Image(systemName: "chevron.right")
                        }.padding(22).foregroundStyle(.white)
                            .background(LinearGradient(colors: kind == .live ? [.teal, .blue.opacity(0.7)] : [.purple.opacity(0.8), .indigo], startPoint: .topLeading, endPoint: .bottomTrailing), in: RoundedRectangle(cornerRadius: 20))
                    }
                }
                if let error = model.error { Text(error).font(.callout).foregroundStyle(.orange); Button("Volver a conectar") { Task { await model.restore() } } }
                Text("Tus favoritos y el punto de reproducción se guardan en este iPhone.").font(.footnote).foregroundStyle(.secondary)
            }.padding(20)
        }.navigationTitle("PIMFLEX TV").navigationBarTitleDisplayMode(.inline)
    }
}

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel
    @State private var confirmReset = false
    var body: some View {
        Form {
            Section("Tu conexión") {
                LabeledContent("Servidor", value: model.account?.server.host ?? "")
                LabeledContent("Acceso", value: model.account?.mode == .xtream ? "Usuario y contraseña" : "Lista M3U")
                if let seconds = Double(model.expiration) { LabeledContent("Vencimiento", value: Date(timeIntervalSince1970: seconds).formatted(date: .abbreviated, time: .omitted)) }
                Button("Actualizar cuenta") { Task { await model.restore() } }
                if let error = model.error { Text(error).foregroundStyle(.orange) }
            }
            Section("En este iPhone") {
                Text("La cuenta se guarda en el llavero de iOS. Favoritos e historial permanecen separados por cuenta.")
                Button("Borrar favoritos e historial", role: .destructive) { confirmReset = true }
            }
            Section("Versión inicial para iPhone") {
                Text("0.1.0 · Prueba técnica")
                Text("Reproduce HLS y archivos compatibles con iOS. Algunos formatos del catálogo Android todavía requieren adaptación.")
                Text("VPN, grabaciones, descargas, multipantalla, Chromecast y acceso por código todavía no están disponibles.")
            }
            Section { Button("Cerrar sesión", role: .destructive) { model.signOut() } }
        }.navigationTitle("Mi cuenta")
            .confirmationDialog("¿Borrar tus favoritos y el historial de esta cuenta?", isPresented: $confirmReset, titleVisibility: .visible) {
                Button("Borrar", role: .destructive) { model.resetPreferences() }
            }
    }
}

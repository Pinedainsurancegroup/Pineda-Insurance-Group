import SwiftUI
import PimflexCore

struct AccountInfoView: View {
    @EnvironmentObject private var model: AppModel
    var body: some View {
        Form {
            Section {
                Brand(height: 65).frame(maxWidth: .infinity).padding(.vertical, 12)
            }.listRowBackground(Color.clear)
            Section("Mi Información") {
                LabeledContent("Usuario", value: model.account?.username.isEmpty == false ? model.account?.username ?? "" : "Lista M3U")
                LabeledContent("Servidor", value: model.account?.server.host ?? "")
                LabeledContent("Tipo de acceso", value: model.account?.mode == .xtream ? "Usuario y contraseña" : "Lista M3U")
                if let timestamp = Double(model.expiration), timestamp.isFinite, timestamp > 0 {
                    LabeledContent("Vencimiento", value: Date(timeIntervalSince1970: timestamp).formatted(date: .abbreviated, time: .omitted))
                }
                Button("Actualizar información") { Task { await model.restore() } }
                if let error = model.error { Text(error).foregroundStyle(.orange) }
            }
        }.scrollContentBackground(.hidden).background { ReferenceBackground() }
            .navigationTitle("Mi Información").navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar)
    }
}

struct SavedAccountsView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var deleting: Account?
    @State private var showDelete = false
    var body: some View {
        List {
            if model.savedAccounts.isEmpty {
                Text("Aún no hay usuarios guardados.").foregroundStyle(.secondary)
            }
            ForEach(model.savedAccounts, id: \.storageID) { account in
                HStack(spacing: 14) {
                    Button {
                        Task {
                            await model.connect(mode: account.mode, server: account.server.absoluteString, username: account.username, password: account.password, allowingInsecureHTTP: account.insecureHTTPEnabled)
                            if model.account == account { dismiss() }
                        }
                    } label: {
                        HStack(spacing: 14) {
                            Image("ReferenceSidebarUsers").resizable().scaledToFit().frame(width: 32, height: 32)
                            VStack(alignment: .leading, spacing: 6) {
                                Text(account.username.isEmpty ? "Lista M3U" : account.username).font(.headline)
                                Text(account.server.host ?? "").font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            if model.account?.storageID == account.storageID { Image(systemName: "checkmark.circle.fill").foregroundStyle(ReferenceTheme.accent) }
                        }.contentShape(Rectangle())
                    }.buttonStyle(.plain).disabled(model.connecting)
                        .accessibilityIdentifier("savedAccount-\(account.username)")
                    Button { deleting = account; showDelete = true } label: {
                        Image(systemName: "trash").frame(width: 36, height: 44)
                    }.buttonStyle(.borderless).accessibilityLabel("Eliminar usuario \(account.username)")
                }.listRowBackground(ReferenceTheme.panel)
            }
            if model.connecting { ProgressView("Conectando…") }
            if let error = model.error { Text(error).foregroundStyle(.orange) }
            Button("AGREGAR USUARIO") { model.signOut(); dismiss() }
                .font(ReferenceTheme.font(15, bold: true)).accessibilityIdentifier("addAccountButton")
        }.listStyle(.insetGrouped).scrollContentBackground(.hidden).background { ReferenceBackground() }
            .navigationTitle("Lista de Usuarios").navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar)
            .confirmationDialog("¿Eliminar este usuario guardado del iPhone?", isPresented: $showDelete, titleVisibility: .visible) {
                Button("Eliminar usuario", role: .destructive) {
                    if let deleting { model.removeAccount(deleting) }
                    deleting = nil
                }
            }
    }
}

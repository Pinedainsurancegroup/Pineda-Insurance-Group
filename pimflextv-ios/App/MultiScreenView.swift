import SwiftUI
import AVFoundation
import UIKit
import PimflexCore

/// Owns every player and the audio session for this grid. Individual tiles never
/// activate/deactivate AVAudioSession, so replacing one cannot silence the others.
@MainActor
private final class MultiScreenPlayback: ObservableObject {
    let slots = (0..<4).map { _ in MultiScreenSlot() }
    @Published private(set) var count = 2
    @Published private(set) var audibleSlot: Int?
    @Published private(set) var suspended = false
    private var audioSessionActive = false

    func setCount(_ newCount: Int) {
        guard newCount == 2 || newCount == 4 else { return }
        count = newCount
        for index in newCount..<slots.count { slots[index].clear() }
        if let audibleSlot, audibleSlot >= newCount { self.audibleSlot = nil }
        reconcileAudio()
        deactivateIfIdle()
    }

    func select(_ channel: MediaItem, at index: Int, account: Account, fixture: Bool) {
        guard (0..<count).contains(index), channel.kind == .live else { return }
        slots[index].prepare(channel)
        if audibleSlot == nil { audibleSlot = index }
        reconcileAudio()
        #if DEBUG
        if fixture {
            slots[index].showPreview()
            return
        }
        #endif
        guard !suspended else { return }
        do {
            let url = try Endpoint.playback(account, item: channel)
            if !audioSessionActive {
                try AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback)
                try AVAudioSession.sharedInstance().setActive(true)
                audioSessionActive = true
            }
            slots[index].play(url)
        } catch {
            slots[index].fail((error as? PimflexError)?.errorDescription ?? "No se pudo activar esta pantalla. Intenta de nuevo.")
            deactivateIfIdle()
        }
    }

    func makeAudible(_ index: Int) {
        guard (0..<count).contains(index), slots[index].channel != nil else { return }
        audibleSlot = index
        reconcileAudio()
    }

    func clear(_ index: Int) {
        guard (0..<count).contains(index) else { return }
        slots[index].clear()
        if audibleSlot == index { audibleSlot = nil }
        reconcileAudio()
        deactivateIfIdle()
    }

    func suspend() {
        for slot in slots { slot.stop() }
        suspended = slots.prefix(count).contains { $0.channel != nil }
        deactivateSession()
    }

    func resume(account: Account, fixture: Bool) {
        suspended = false
        for index in 0..<count {
            if let channel = slots[index].channel {
                select(channel, at: index, account: account, fixture: fixture)
            }
        }
    }

    private func reconcileAudio() {
        if audibleSlot == nil { audibleSlot = (0..<count).first { slots[$0].channel != nil } }
        // Mute all players first, including hidden slots, before enabling one.
        for slot in slots { slot.player.isMuted = true }
        if let audibleSlot, (0..<count).contains(audibleSlot) { slots[audibleSlot].player.isMuted = false }
    }

    private func deactivateIfIdle() {
        if slots.allSatisfy({ $0.player.currentItem == nil }) { deactivateSession() }
    }

    private func deactivateSession() {
        guard audioSessionActive else { return }
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        audioSessionActive = false
    }
}

@MainActor
private final class MultiScreenSlot: ObservableObject {
    let player = AVPlayer()
    @Published private(set) var channel: MediaItem?
    @Published private(set) var waiting = false
    @Published private(set) var error: String?
    #if DEBUG
    @Published private(set) var preview = false
    #endif
    private var status: NSKeyValueObservation?
    private var timeControl: NSKeyValueObservation?
    private var failureObserver: NSObjectProtocol?
    private var stalledObserver: NSObjectProtocol?
    private var timeout: Task<Void, Never>?

    init() { player.isMuted = true; player.allowsExternalPlayback = false }

    func prepare(_ channel: MediaItem) {
        stop()
        self.channel = channel
        #if DEBUG
        preview = false
        #endif
    }

    #if DEBUG
    func showPreview() { preview = true }
    #endif

    func play(_ url: URL) {
        waiting = true; error = nil
        let item = AVPlayerItem(url: url)
        player.replaceCurrentItem(with: item)
        status = item.observe(\.status, options: [.initial, .new]) { [weak self] item, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                if item.status == .failed { self.fail("No se pudo abrir el canal. Revisa el formato y las conexiones disponibles de tu cuenta.") }
            }
        }
        timeControl = player.observe(\.timeControlStatus, options: [.new]) { [weak self] player, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item, self.error == nil else { return }
                switch player.timeControlStatus {
                case .playing: self.waiting = false; self.timeout?.cancel(); self.timeout = nil
                case .waitingToPlayAtSpecifiedRate: self.waiting = true; self.armTimeout(item)
                case .paused: self.waiting = false; self.timeout?.cancel(); self.timeout = nil
                @unknown default: break
                }
            }
        }
        failureObserver = NotificationCenter.default.addObserver(forName: .AVPlayerItemFailedToPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                self.fail("La transmisión se interrumpió. Puedes volver a intentarlo.")
            }
        }
        stalledObserver = NotificationCenter.default.addObserver(forName: .AVPlayerItemPlaybackStalled, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item, self.error == nil else { return }
                self.waiting = true; self.armTimeout(item)
            }
        }
        armTimeout(item)
        player.play()
    }

    func fail(_ message: String) {
        stop()
        error = message
    }

    func stop() {
        status = nil; timeControl = nil
        timeout?.cancel(); timeout = nil
        for observer in [failureObserver, stalledObserver].compactMap({ $0 }) {
            NotificationCenter.default.removeObserver(observer)
        }
        failureObserver = nil; stalledObserver = nil
        player.pause(); player.replaceCurrentItem(with: nil)
        waiting = false; error = nil
    }

    func clear() {
        stop(); channel = nil
        #if DEBUG
        preview = false
        #endif
    }

    private func armTimeout(_ item: AVPlayerItem) {
        guard timeout == nil else { return }
        timeout = Task { [weak self] in
            do { try await Task.sleep(nanoseconds: 30_000_000_000) } catch { return }
            guard let self, self.player.currentItem === item, self.waiting else { return }
            self.fail("El canal tardó demasiado en responder.")
        }
    }
}

struct MultiScreenView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var playback = MultiScreenPlayback()
    @State private var channels: [MediaItem] = []
    @State private var loading = true
    @State private var error: String?
    @State private var sessionAccount: Account?
    @State private var target: ChannelTarget?

    private struct ChannelTarget: Identifiable { let id: Int }

    var body: some View {
        GeometryReader { geometry in
            ScrollView {
                VStack(spacing: 16) {
                    Picker("Pantallas", selection: Binding(get: { playback.count }, set: { playback.setCount($0) })) {
                        Text("2 pantallas").tag(2)
                        Text("4 pantallas").tag(4)
                    }.pickerStyle(.segmented).accessibilityIdentifier("multiScreenCount")
                    Text("Elige los canales. El audio se escucha de una pantalla a la vez.")
                        .font(.footnote).foregroundStyle(.secondary)
                    if loading { ProgressView("Cargando canales…") }
                    if let error {
                        VStack(spacing: 8) {
                            Text(error).font(.callout)
                            Button("Cargar canales de nuevo") { Task { await loadChannels(refresh: true) } }
                        }.multilineTextAlignment(.center)
                    }
                    if playback.suspended {
                        Button("Reanudar pantallas") {
                            guard scenePhase == .active, let account = model.account, account == sessionAccount else { return }
                            playback.resume(account: account, fixture: model.usesTestFixtures)
                        }.buttonStyle(.borderedProminent).accessibilityIdentifier("resumeMultiScreen")
                    }
                    LazyVGrid(columns: columns(for: geometry.size.width), spacing: 14) {
                        ForEach(0..<playback.count, id: \.self) { index in
                            MultiScreenTile(slot: playback.slots[index], index: index,
                                            audible: playback.audibleSlot == index, suspended: playback.suspended,
                                            canSelect: !loading && !channels.isEmpty,
                                            select: { target = ChannelTarget(id: index) },
                                            retry: {
                                                if let channel = playback.slots[index].channel { select(channel, at: index) }
                                            },
                                            audio: { playback.makeAudible(index) },
                                            clear: { playback.clear(index) })
                        }
                    }
                    if !loading && channels.isEmpty && error == nil {
                        Text("Tu cuenta no devolvió canales de TV en directo.").font(.callout)
                    }
                }.padding(16)
            }
        }.background { ReferenceBackground() }
            .navigationTitle("PANTALLA MÚLTIPLE").navigationBarTitleDisplayMode(.inline)
            .toolbar(.visible, for: .navigationBar)
            .task(id: model.account?.storageID) { await loadChannels() }
            .sheet(item: $target) { selection in
                MultiScreenChannelPicker(channels: channels) { channel in
                    select(channel, at: selection.id)
                    target = nil
                }
            }
            .onDisappear { playback.suspend() }
            .onChange(of: scenePhase) { if $0 == .background { playback.suspend() } }
            .onChange(of: model.account) { _ in playback.suspend(); target = nil; sessionAccount = nil }
    }

    private func columns(for width: CGFloat) -> [GridItem] {
        Array(repeating: GridItem(.flexible(), spacing: 14), count: playback.count == 4 || width > 650 ? 2 : 1)
    }

    private func select(_ channel: MediaItem, at index: Int) {
        guard scenePhase == .active, let account = model.account, account == sessionAccount else { return }
        playback.select(channel, at: index, account: account, fixture: model.usesTestFixtures)
    }

    @MainActor private func loadChannels(refresh: Bool = false) async {
        guard let account = model.account else { loading = false; return }
        sessionAccount = account; loading = true; error = nil
        defer { loading = false }
        do {
            let (_, entries) = try await model.catalog(.live, refresh: refresh)
            try Task.checkCancellation()
            guard model.account == account else { return }
            channels = entries
        } catch is CancellationError { }
        catch { if model.account == account { self.error = model.message(error) } }
    }
}

private struct MultiScreenTile: View {
    @ObservedObject var slot: MultiScreenSlot
    let index: Int
    let audible: Bool
    let suspended: Bool
    let canSelect: Bool
    let select: () -> Void
    let retry: () -> Void
    let audio: () -> Void
    let clear: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text(slot.channel?.name ?? "Pantalla \(index + 1)").font(.subheadline.bold()).lineLimit(1)
                Spacer(minLength: 4)
                if slot.channel != nil {
                    Button(action: clear) { Image(systemName: "xmark").frame(width: 36, height: 36) }
                        .accessibilityLabel("Vaciar pantalla \(index + 1)")
                }
            }.padding(.horizontal, 10).frame(minHeight: 40)
            picture.aspectRatio(16.0 / 9.0, contentMode: .fit)
            HStack(spacing: 0) {
                Button(action: select) {
                    Label("Canal", systemImage: "list.bullet").font(.caption.bold()).frame(maxWidth: .infinity, minHeight: 44)
                }.disabled(!canSelect).accessibilityIdentifier("selectChannel-\(index)")
                Button(action: audio) {
                    Image(systemName: audible ? "speaker.wave.2.fill" : "speaker.slash.fill")
                        .frame(maxWidth: .infinity, minHeight: 44)
                }.disabled(slot.channel == nil)
                    .foregroundStyle(audible ? ReferenceTheme.accent : .white.opacity(0.6))
                    .accessibilityLabel("Audio de pantalla \(index + 1)")
                    .accessibilityValue(audible ? "Activado" : "Silenciado")
                    .accessibilityIdentifier("audioSlot-\(index)")
            }
        }.background(ReferenceTheme.panel.opacity(0.95), in: RoundedRectangle(cornerRadius: 10))
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(audible ? ReferenceTheme.accent : .white.opacity(0.16), lineWidth: audible ? 2 : 1))
    }

    @ViewBuilder private var picture: some View {
        #if DEBUG
        if slot.preview {
            ZStack {
                Color.black
                VStack(spacing: 8) {
                    Image(systemName: "tv").font(.title)
                    Text("Vista previa · sin transmisión").font(.caption).multilineTextAlignment(.center)
                }.padding(12)
            }.accessibilityIdentifier("multiScreenPreview-\(index)")
        } else { livePicture }
        #else
        livePicture
        #endif
    }

    private var livePicture: some View {
        ZStack {
            Color.black
            MultiScreenVideoSurface(player: slot.player)
            if slot.channel == nil {
                Button("Elegir canal", action: select).disabled(!canSelect)
            } else if let error = slot.error {
                VStack(spacing: 8) {
                    Text(error).font(.caption).multilineTextAlignment(.center)
                    Button("Reintentar", action: retry).font(.caption.bold())
                }.padding(10).frame(maxWidth: .infinity, maxHeight: .infinity).background(.black.opacity(0.88))
            } else if suspended { Text("En pausa").font(.caption) }
            else if slot.waiting { ProgressView().tint(.white) }
        }
    }
}

private struct MultiScreenChannelPicker: View {
    @Environment(\.dismiss) private var dismiss
    @State private var search = ""
    let channels: [MediaItem]
    let select: (MediaItem) -> Void
    private var filtered: [MediaItem] {
        search.isEmpty ? channels : channels.filter { $0.name.localizedCaseInsensitiveContains(search) }
    }
    var body: some View {
        NavigationStack {
            List(filtered) { channel in
                Button { select(channel) } label: { Text(channel.name).foregroundStyle(.primary) }
                    .accessibilityIdentifier("multiChannel-\(channel.id)")
            }.searchable(text: $search, prompt: "Buscar canal")
                .navigationTitle("Elegir canal").navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Cancelar") { dismiss() } }
        }
    }
}

private struct MultiScreenVideoSurface: UIViewRepresentable {
    let player: AVPlayer
    func makeUIView(context: Context) -> MultiScreenVideoLayer {
        let view = MultiScreenVideoLayer()
        view.playerLayer.videoGravity = .resizeAspect
        view.playerLayer.player = player
        return view
    }
    func updateUIView(_ view: MultiScreenVideoLayer, context: Context) { view.playerLayer.player = player }
    static func dismantleUIView(_ view: MultiScreenVideoLayer, coordinator: ()) { view.playerLayer.player = nil }
}

private final class MultiScreenVideoLayer: UIView {
    override class var layerClass: AnyClass { AVPlayerLayer.self }
    var playerLayer: AVPlayerLayer { layer as! AVPlayerLayer }
}

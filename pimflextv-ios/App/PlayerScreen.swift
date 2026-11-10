import SwiftUI
import AVKit
import PimflexCore

@MainActor
final class PlaybackModel: ObservableObject {
    let player = AVPlayer()
    @Published var error: String?
    @Published var waiting = true
    private var status: NSKeyValueObservation?
    private var timeControl: NSKeyValueObservation?
    private var timer: Any?
    private var end: NSObjectProtocol?
    private var fail: NSObjectProtocol?
    private var stalled: NSObjectProtocol?
    private var startTimeout: Task<Void, Never>?
    private var save: ((Double) -> Void)?

    func start(url: URL, resume: Double, save: @escaping (Double) -> Void) {
        stop(); self.save = save; waiting = true; error = nil
        do { try AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback); try AVAudioSession.sharedInstance().setActive(true) }
        catch { self.error = "No se pudo activar el audio."; waiting = false; return }
        let item = AVPlayerItem(url: url)
        player.replaceCurrentItem(with: item)
        player.allowsExternalPlayback = true
        status = item.observe(\.status, options: [.initial, .new]) { [weak self] item, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                if item.status == .failed {
                    self.waiting = false; self.error = "No se pudo reproducir. Comprueba el canal y su compatibilidad con iPhone."; self.startTimeout?.cancel()
                } else if item.status == .readyToPlay {
                    guard self.error == nil else { return }
                    self.waiting = true
                    let duration = item.duration.seconds
                    if resume > 5 && duration.isFinite && resume < duration - 10 {
                        await self.player.seek(to: CMTime(seconds: resume, preferredTimescale: 600))
                    }
                    if self.player.currentItem === item { self.player.play() }
                }
            }
        }
        timeControl = player.observe(\.timeControlStatus, options: [.new]) { [weak self] player, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item, self.error == nil else { return }
                if player.timeControlStatus == .playing {
                    self.waiting = false; self.startTimeout?.cancel()
                } else if player.timeControlStatus == .waitingToPlayAtSpecifiedRate {
                    self.waiting = true; self.armTimeout(for: item)
                } else if player.timeControlStatus == .paused {
                    self.waiting = false; self.startTimeout?.cancel()
                }
            }
        }
        stalled = NotificationCenter.default.addObserver(forName: .AVPlayerItemPlaybackStalled, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item, self.error == nil else { return }
                self.waiting = true; self.armTimeout(for: item)
            }
        }
        timer = player.addPeriodicTimeObserver(forInterval: CMTime(seconds: 10, preferredTimescale: 1), queue: .main) { [weak self] time in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }; self.save?(time.seconds)
            }
        }
        end = NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }; self.save?(0); self.save = nil
            }
        }
        fail = NotificationCenter.default.addObserver(forName: .AVPlayerItemFailedToPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                self.waiting = false; self.startTimeout?.cancel()
                self.error = "La transmisión se interrumpió. Intenta reproducirla de nuevo."
            }
        }
        armTimeout(for: item)
    }
    private func armTimeout(for item: AVPlayerItem) {
        startTimeout?.cancel()
        startTimeout = Task { [weak self] in
            do { try await Task.sleep(nanoseconds: 30_000_000_000) } catch { return }
            guard let self, self.waiting, self.player.currentItem === item else { return }
            self.player.pause(); self.waiting = false; self.error = "El canal tardó demasiado en responder. Intenta de nuevo."
        }
    }
    func stop() {
        save?(player.currentTime().seconds); save = nil; player.pause()
        status = nil; timeControl = nil; startTimeout?.cancel(); startTimeout = nil
        if let timer { player.removeTimeObserver(timer) }; timer = nil
        for observer in [end, fail, stalled].compactMap({ $0 }) { NotificationCenter.default.removeObserver(observer) }
        end = nil; fail = nil; stalled = nil; player.replaceCurrentItem(with: nil)
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}

struct NativePlayer: UIViewControllerRepresentable {
    let player: AVPlayer
    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.player = player
        // PiP intentionally disabled until lifecycle/device tests cover background dismissal.
        controller.allowsPictureInPicturePlayback = false
        return controller
    }
    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) { controller.player = player }
    static func dismantleUIViewController(_ controller: AVPlayerViewController, coordinator: ()) { controller.player = nil }
}

struct PlayerScreen: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var playback = PlaybackModel()
    @StateObject private var compatible = CompatiblePlaybackModel()
    @State private var usesCompatible = false
    @State private var playbackAccount: Account?
    let item: MediaItem
    var body: some View {
        ZStack(alignment: .topLeading) {
            Color.black.ignoresSafeArea()
            if usesCompatible {
                CompatibleVideoSurface(playback: compatible).ignoresSafeArea()
                VStack { Spacer(); CompatiblePlaybackControls(playback: compatible) }
            } else { NativePlayer(player: playback.player).ignoresSafeArea() }
            if usesCompatible ? compatible.waiting : playback.waiting {
                ProgressView("Abriendo transmisión…").tint(.white).frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            if let error = usesCompatible ? compatible.error : playback.error {
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle").font(.largeTitle)
                    Text(error).multilineTextAlignment(.center)
                    Button("Reintentar") { start(forceCompatible: usesCompatible) }.buttonStyle(.borderedProminent).tint(.cyan).foregroundStyle(.black)
                    if !usesCompatible {
                        Button("Probar modo compatible") { start(forceCompatible: true) }.buttonStyle(.bordered)
                    }
                }.foregroundStyle(.white).padding(30).frame(maxWidth: .infinity, maxHeight: .infinity).background(.black.opacity(0.9))
            }
            Button { dismiss() } label: { Label("Cerrar", systemImage: "xmark").padding(12).background(.ultraThinMaterial, in: Capsule()) }.foregroundStyle(.white).padding(16).accessibilityIdentifier("playerClose")
        }.task { start() }
            .onDisappear { playback.stop(); compatible.stop() }
            .onChange(of: scenePhase) { phase in
                if phase == .background, model.account == playbackAccount {
                    if usesCompatible { compatible.savePosition() }
                    else { model.savePosition(playback.player.currentTime().seconds, item: item) }
                }
            }
    }
    private func start(forceCompatible: Bool = false) {
        guard let account = model.account else { return }
        playbackAccount = account
        do {
            let url: URL
            #if DEBUG
            if model.usesTestFixtures, ProcessInfo.processInfo.arguments.contains("--test-mkv-playback") {
                guard let fixture = Bundle.main.url(forResource: "PlaybackFixture", withExtension: "mkv") else { throw PimflexError.invalidResponse }
                url = fixture
            } else { url = try Endpoint.playback(account, item: item) }
            #else
            url = try Endpoint.playback(account, item: item)
            #endif
            playback.stop(); compatible.stop()
            usesCompatible = forceCompatible || PlaybackEngine.forMediaURL(url) == .compatible
            let save: (Double) -> Void = {
                guard model.account == account else { return }
                model.savePosition($0, item: item)
            }
            if usesCompatible { compatible.start(url: url, resume: model.positions[item.id] ?? 0, save: save) }
            else { playback.start(url: url, resume: model.positions[item.id] ?? 0, save: save) }
        } catch {
            playback.waiting = false; compatible.waiting = false
            if usesCompatible { compatible.error = model.message(error) }
            else { playback.error = model.message(error) }
        }
    }
}

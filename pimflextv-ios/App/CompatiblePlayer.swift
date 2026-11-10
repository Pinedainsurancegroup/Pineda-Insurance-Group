import SwiftUI
import AVFoundation
import MobileVLCKit

@MainActor
final class CompatiblePlaybackModel: NSObject, ObservableObject, VLCMediaPlayerDelegate {
    // Suppress backend logs, which can include a provider URL with credentials.
    private var instance: VLCMediaPlayer?
    var player: VLCMediaPlayer {
        if let instance { return instance }
        let value = VLCMediaPlayer(options: ["--quiet", "--no-video-title-show"])
        value.delegate = self; instance = value
        return value
    }
    @Published var waiting = true
    @Published var error: String?
    @Published var playing = false
    @Published var seconds = 0.0
    @Published var duration = 0.0
    @Published var seekable = false
    @Published var hasVideo = false
    private var active = false
    private var needsPlay = false
    private var userPaused = false
    private var lastObservedSeconds = 0.0
    private var lastProgressTime = Date.timeIntervalSinceReferenceDate
    private var ended = false
    private var pendingResume = 0.0
    private var pendingSeek: (target: Double, origin: Double)?
    private var seekWhenPlaying = false
    private var save: ((Double) -> Void)?
    private var pollTask: Task<Void, Never>?
    private var timeout: Task<Void, Never>?

    deinit { pollTask?.cancel(); timeout?.cancel() }

    func start(url: URL, resume: Double, save: @escaping (Double) -> Void) {
        stop()
        self.save = save; pendingResume = resume.isFinite ? max(0, resume) : 0
        waiting = true; error = nil; active = true; ended = false; needsPlay = true
        seconds = 0; duration = 0; hasVideo = false
        userPaused = false; lastObservedSeconds = 0
        pendingSeek = nil; seekWhenPlaying = false
        lastProgressTime = Date.timeIntervalSinceReferenceDate
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch { self.error = "No se pudo activar el audio."; waiting = false; return }
        player.media = VLCMedia(url: url)
        playWhenAttached()
        armTimeout()
        pollTask = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                do { try await Task.sleep(nanoseconds: 250_000_000) } catch { return }
                self?.refresh()
            }
        }
    }

    func attach(_ view: UIView) {
        player.drawable = view
        playWhenAttached()
    }
    private func playWhenAttached() {
        guard let player = instance, active, needsPlay, player.drawable != nil, player.media != nil else { return }
        needsPlay = false
        player.play()
    }

    nonisolated func mediaPlayerStateChanged(_ notification: Notification!) {
        Task { @MainActor [weak self] in self?.refresh() }
    }
    nonisolated func mediaPlayerTimeChanged(_ notification: Notification!) {
        Task { @MainActor [weak self] in self?.refresh() }
    }

    private func refresh() {
        guard active, let player = instance else { return }
        let actualSeconds = max(0, Double(player.time.intValue) / 1000)
        if let pending = pendingSeek {
            // VLCKit's time getter is event-cached and may stay at the previous
            // frame during a paused seek. Hold the selected position until the
            // actual playback clock reaches it, rather than snapping the slider back.
            let reached = pending.target >= pending.origin ? actualSeconds >= pending.target - 0.75 : actualSeconds <= pending.target + 0.75
            if reached { pendingSeek = nil; seekWhenPlaying = false }
        }
        seconds = pendingSeek?.target ?? actualSeconds
        let now = Date.timeIntervalSinceReferenceDate
        if abs(actualSeconds - lastObservedSeconds) > 0.05 {
            lastObservedSeconds = actualSeconds; lastProgressTime = now
        }
        duration = max(0, Double(player.media?.length.intValue ?? 0) / 1000)
        seekable = player.isSeekable
        hasVideo = player.hasVideoOut && player.videoSize.width > 0
        playing = player.isPlaying
        if playing, seekWhenPlaying, let pending = pendingSeek {
            seekWhenPlaying = false
            player.time = VLCTime(int: Int32(min(pending.target * 1000, Double(Int32.max))))
        }
        switch player.state {
        case .playing:
            waiting = false; timeout?.cancel(); timeout = nil
            if pendingResume > 5, duration > pendingResume + 10, seekable {
                let position = pendingResume; pendingResume = 0; seek(to: position)
            } else if duration > 0 { pendingResume = 0 }
        case .paused:
            waiting = false; timeout?.cancel(); timeout = nil
        case .opening, .buffering:
            // VLCKit caches its last buffering event, including 100%, even while
            // frames are playing. Use output/clock progress and explicit pause to
            // avoid a permanent spinner or an erroneous 30-second timeout.
            waiting = !userPaused && ((!hasVideo && seconds <= 0) || (playing && now - lastProgressTime > 3))
            if waiting { armTimeout() }
            else { timeout?.cancel(); timeout = nil }
        case .ended:
            if !ended { save?(0); ended = true }
            pendingSeek = nil; seekWhenPlaying = false
            waiting = false; playing = false; timeout?.cancel(); timeout = nil
        case .error:
            waiting = false; playing = false
            error = "No se pudo reproducir esta transmisión. Reintenta o prueba otro título."
            timeout?.cancel(); timeout = nil
        default: break
        }
    }

    func togglePause() {
        guard active, error == nil else { return }
        if player.isPlaying { userPaused = true; player.pause() }
        else {
            userPaused = false; lastProgressTime = Date.timeIntervalSinceReferenceDate
            if ended { ended = false; player.stop() }
            seekWhenPlaying = pendingSeek != nil
            player.play()
        }
        refresh()
    }
    func seek(to position: Double) {
        guard active, seekable, position.isFinite else { return }
        let value = min(max(0, position), max(0, duration - 0.5))
        pendingSeek = (value, max(0, Double(player.time.intValue) / 1000))
        player.time = VLCTime(int: Int32(min(value * 1000, Double(Int32.max))))
        // libVLC applies a paused seek when a decoded frame is requested. Step
        // once to update the picture and clock while preserving the pause state.
        if !player.isPlaying { player.gotoNextFrame() }
        seconds = value
    }
    func savePosition() { if active, !ended { save?(seconds) } }

    private func armTimeout() {
        guard timeout == nil else { return }
        timeout = Task { @MainActor [weak self] in
            do { try await Task.sleep(nanoseconds: 30_000_000_000) } catch { return }
            guard let self, self.active, self.waiting else { return }
            self.error = "El video tardó demasiado en responder. Intenta de nuevo."
            self.waiting = false; self.playing = false
            self.player.stop()
        }
    }
    func stop() {
        savePosition()
        active = false; needsPlay = false; save = nil
        pendingSeek = nil; seekWhenPlaying = false
        pollTask?.cancel(); pollTask = nil
        timeout?.cancel(); timeout = nil
        instance?.stop(); instance?.media = nil
        playing = false; waiting = false
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}

struct CompatibleVideoSurface: UIViewRepresentable {
    @ObservedObject var playback: CompatiblePlaybackModel
    func makeCoordinator() -> CompatiblePlaybackModel { playback }
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .black
        view.isAccessibilityElement = true
        view.accessibilityLabel = "Video"
        view.accessibilityIdentifier = "compatibleVideoSurface"
        playback.attach(view)
        return view
    }
    func updateUIView(_ view: UIView, context: Context) {
        view.accessibilityValue = playback.playing && playback.hasVideo && playback.seconds >= 1 ? "Reproduciendo" : playback.waiting ? "Cargando" : "En pausa"
    }
    static func dismantleUIView(_ view: UIView, coordinator: CompatiblePlaybackModel) {
        if let current = coordinator.player.drawable as? UIView, current === view {
            coordinator.player.drawable = nil
        }
    }
}

struct CompatiblePlaybackControls: View {
    @ObservedObject var playback: CompatiblePlaybackModel
    private func clock(_ value: Double) -> String {
        let seconds = max(0, Int(value.isFinite ? value : 0))
        return String(format: "%d:%02d", seconds / 60, seconds % 60)
    }
    var body: some View {
        VStack(spacing: 10) {
            Slider(value: Binding(get: { min(playback.seconds, max(1, playback.duration)) }, set: { playback.seek(to: $0) }), in: 0...max(1, playback.duration))
                .disabled(!playback.seekable || playback.duration <= 0)
                .accessibilityLabel("Posición del video")
            HStack(spacing: 28) {
                Text(clock(playback.seconds)).monospacedDigit().accessibilityIdentifier("playbackPosition")
                Spacer()
                Button { playback.seek(to: playback.seconds - 10) } label: { Image(systemName: "gobackward.10") }
                    .disabled(!playback.seekable).accessibilityLabel("Retroceder 10 segundos")
                Button { playback.togglePause() } label: { Image(systemName: playback.playing ? "pause.fill" : "play.fill") }
                    .accessibilityLabel(playback.playing ? "Pausar" : "Reproducir")
                    .accessibilityIdentifier("compatiblePlayPause")
                Button { playback.seek(to: playback.seconds + 10) } label: { Image(systemName: "goforward.10") }
                    .disabled(!playback.seekable).accessibilityLabel("Adelantar 10 segundos")
                Spacer()
                Text(clock(playback.duration)).monospacedDigit()
            }.font(.title3).buttonStyle(.plain)
        }.foregroundStyle(.white).tint(.cyan).padding(16).background(.black.opacity(0.7), in: RoundedRectangle(cornerRadius: 16)).padding()
    }
}

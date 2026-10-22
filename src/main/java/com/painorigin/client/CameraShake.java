package com.painorigin.client;

import com.painorigin.PainClientConfig;
import net.minecraft.util.Mth;
import net.minecraftforge.client.event.ViewportEvent;

/**
 * Small decaying camera shake (pitch / yaw / roll noise) triggered by the Shinra Tensei flash and the
 * Chibaku Tensei collapse when they happen near the local player. Disabled by
 * {@code camera.shake = false} in painorigin-client.toml; strength via {@code camera.shakeStrength}.
 */
public final class CameraShake {
    private static float amplitude;
    private static int ticksLeft;
    private static int totalTicks = 1;
    private static int clock;

    private CameraShake() {}

    /** Starts (or strengthens) a shake. {@code amplitudeDegrees} is the peak angle at the start. */
    public static void trigger(float amplitudeDegrees, int ticks) {
        if (!PainClientConfig.CAMERA_SHAKE.get()) {
            return;
        }
        double strength = PainClientConfig.CAMERA_SHAKE_STRENGTH.get();
        float amp = (float) (amplitudeDegrees * strength);
        if (amp < 0.01F || ticks <= 0) {
            return;
        }
        float running = ticksLeft > 0 ? amplitude * ((float) ticksLeft / (float) totalTicks) : 0.0F;
        if (amp >= running) {
            amplitude = amp;
            ticksLeft = ticks;
            totalTicks = ticks;
        }
    }

    /** Called once per client tick. */
    public static void tick() {
        clock++;
        if (ticksLeft > 0) {
            ticksLeft--;
        }
    }

    public static void apply(ViewportEvent.ComputeCameraAngles event) {
        if (ticksLeft <= 0) {
            return;
        }
        double partial = event.getPartialTick();
        float k = Mth.clamp((ticksLeft - (float) partial) / (float) totalTicks, 0.0F, 1.0F);
        float a = amplitude * k * k;
        double t = clock + partial;
        event.setPitch(event.getPitch() + (float) (Math.sin(t * 2.9) + 0.5 * Math.sin(t * 7.3 + 1.0)) * a);
        event.setYaw(event.getYaw() + (float) (Math.sin(t * 3.7 + 2.0) + 0.5 * Math.sin(t * 6.1)) * a * 0.7F);
        event.setRoll(event.getRoll() + (float) Math.sin(t * 4.3 + 0.5) * a * 0.8F);
    }
}

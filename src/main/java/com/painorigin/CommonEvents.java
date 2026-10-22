package com.painorigin;

import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Game-bus event handlers (logical server). */
@Mod.EventBusSubscriber(modid = PainOrigin.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class CommonEvents {
    private CommonEvents() {}

    @SubscribeEvent
    public static void onRegisterCommands(RegisterCommandsEvent event) {
        PainCommands.register(event.getDispatcher());
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase == TickEvent.Phase.END) {
            ChibakuManager.tick(event.getServer());
            Fx.tick(event.getServer());
        }
    }

    /** The caster left the game: the technique ends. */
    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            ChibakuManager.cancelFor(player.getUUID(), "logout");
        }
    }

    /** The caster died: the technique ends. */
    @SubscribeEvent
    public static void onDeath(LivingDeathEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            ChibakuManager.cancelFor(player.getUUID(), "death");
        }
    }

    /** The caster changed dimension: the technique ends. */
    @SubscribeEvent
    public static void onDimensionChange(PlayerEvent.PlayerChangedDimensionEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            ChibakuManager.cancelFor(player.getUUID(), "dimension");
        }
    }

    /** A heavy hit (after armor) interrupts the channelling caster. */
    @SubscribeEvent
    public static void onDamage(LivingDamageEvent event) {
        if (event.getEntity() instanceof ServerPlayer player && ChibakuManager.isActive(player.getUUID())) {
            double limit = PainConfig.CHIBAKU_INTERRUPT_DAMAGE.get();
            if (limit > 0.0 && event.getAmount() >= limit) {
                ChibakuManager.cancelFor(player.getUUID(), "damage");
            }
        }
    }

    @SubscribeEvent
    public static void onServerStopping(ServerStoppingEvent event) {
        ChibakuManager.cancelAll("shutdown");
    }

    /** Drop all static state so that a new world in the same JVM (single player) starts clean. */
    @SubscribeEvent
    public static void onServerStopped(ServerStoppedEvent event) {
        ChibakuManager.reset();
        Fx.reset();
    }
}

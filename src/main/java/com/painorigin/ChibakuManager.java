package com.painorigin;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Chibaku Tensei, the phased technique. It is started by the JSON power through
 * {@code /painorigin chibaku start} (the JSON already charged the chakra and started the cooldown) and
 * then driven by the server tick.
 *
 * <pre>
 *  phase         share of durationTicks   what happens
 *  ACTIVATION    0-10%                    the caster channels; a vortex of aura gathers around him
 *  CORE          10-25%                   a dark core appears {coreHeight} blocks above and starts to grow
 *  FIELD         25-55%                   gravity field: creatures in {fieldRadius} are dragged toward the axis
 *  DEBRIS        55-80%                   terrain pieces fly into the core; creatures are lifted toward it
 *  FORMATION     80-100%                  the core becomes a rock-like satellite; captured creatures are held
 *  FINAL         at durationTicks         collapse: damage + knockback, release, (optionally) real blocks removed
 * </pre>
 *
 * <p><b>Debris is simulated by default</b>: {@code chibaku.maxBlocks} ground blocks are only used as the
 * starting points of debris particles; nothing is removed from the world. With the experimental
 * {@code chibaku.realBlocks = true} the same blocks are really removed - once, at the final collapse, after
 * passing {@link BlockSafety}. Cancelling before that moment therefore never changes the world.
 *
 * <p>The session is cancelled when the caster dies, logs out, changes dimension, moves farther than
 * {@code interruptDistance}, takes a hit of at least {@code interruptDamage}, or the server stops.
 * Creatures that were lifted get fall protection until they land (or 10 s), so the only damage they take is
 * the collapse itself.
 */
public final class ChibakuManager {
    /** Entity types that are never pulled or damaged (data/painorigin/tags/entity_types/chibaku_immune.json). */
    public static final TagKey<EntityType<?>> IMMUNE =
            TagKey.create(Registries.ENTITY_TYPE, PainOrigin.id("chibaku_immune"));

    private enum Phase {
        ACTIVATION("activation"),
        CORE("core"),
        FIELD("field"),
        DEBRIS("debris"),
        FORMATION("formation"),
        FINAL("final");

        final String key;

        Phase(String key) {
            this.key = key;
        }
    }

    private static final class Session {
        final MinecraftServer server;
        final UUID caster;
        final ResourceKey<Level> dimension;
        final Vec3 anchor;
        final Vec3 core;
        final int duration;
        final double fieldRadius;
        final int maxAirborne;
        final int liftStart;
        int tick;
        Phase phase;
        int nextSource;
        final List<BlockPos> sources = new ArrayList<>();
        final Map<UUID, Integer> airborne = new HashMap<>();
        final Set<UUID> touched = new HashSet<>();

        Session(MinecraftServer server, UUID caster, ResourceKey<Level> dimension, Vec3 anchor, Vec3 core,
                int duration, double fieldRadius, int maxAirborne) {
            this.server = server;
            this.caster = caster;
            this.dimension = dimension;
            this.anchor = anchor;
            this.core = core;
            this.duration = duration;
            this.fieldRadius = fieldRadius;
            this.maxAirborne = maxAirborne;
            this.liftStart = Math.max((int) Math.round(duration * 0.55), duration - maxAirborne);
        }
    }

    private static final class Protect {
        final ResourceKey<Level> dimension;
        int ticksLeft = 200;
        boolean sawAir;

        Protect(ResourceKey<Level> dimension) {
            this.dimension = dimension;
        }
    }

    private static final Map<UUID, Session> SESSIONS = new LinkedHashMap<>();
    private static final Map<UUID, Protect> FALL_PROTECT = new HashMap<>();

    private ChibakuManager() {}

    // ------------------------------------------------------------------------------------------
    // public API
    // ------------------------------------------------------------------------------------------

    public static boolean isActive(UUID caster) {
        return SESSIONS.containsKey(caster);
    }

    public static int activeCount() {
        return SESSIONS.size();
    }

    /** Starts the technique for {@code player}. @return false (with a message) when it cannot start. */
    public static boolean start(ServerPlayer player) {
        if (!PainConfig.CHIBAKU_ENABLED.get()) {
            player.displayClientMessage(Component.translatable("painorigin.chibaku.disabled"), true);
            return false;
        }
        if (SESSIONS.containsKey(player.getUUID())) {
            player.displayClientMessage(Component.translatable("painorigin.chibaku.already_active"), true);
            return false;
        }
        if (SESSIONS.size() >= PainConfig.CHIBAKU_MAX_SESSIONS.get()) {
            player.displayClientMessage(Component.translatable("painorigin.chibaku.busy"), true);
            return false;
        }
        MinecraftServer server = player.getServer();
        if (server == null) {
            return false;
        }
        ServerLevel level = (ServerLevel) player.level();
        Vec3 anchor = player.position();
        double wanted = PainConfig.CHIBAKU_CORE_HEIGHT.get();
        double room = level.getMaxBuildHeight() - 4.0 - anchor.y;
        double height = Math.max(3.0, Math.min(wanted, room));
        Vec3 core = new Vec3(anchor.x, anchor.y + height, anchor.z);

        Session session = new Session(server, player.getUUID(), level.dimension(), anchor, core,
                PainConfig.CHIBAKU_DURATION.get(), PainConfig.CHIBAKU_FIELD_RADIUS.get(),
                PainConfig.CHIBAKU_MAX_AIRBORNE.get());
        SESSIONS.put(session.caster, session);
        player.displayClientMessage(Component.translatable("painorigin.chibaku.start"), true);
        playSound(level, anchor, ModSounds.SHINRA_CHARGE.get(), 3.0F, 0.6F);
        return true;
    }

    /** Cancels the caster's technique. @return false when none was running. */
    public static boolean cancelFor(UUID caster, String reason) {
        Session session = SESSIONS.get(caster);
        if (session == null) {
            return false;
        }
        cancel(session, reason);
        return true;
    }

    public static void cancelAll(String reason) {
        for (Session session : new ArrayList<>(SESSIONS.values())) {
            cancel(session, reason);
        }
    }

    /** Forget everything (called when a world is closed). */
    public static void reset() {
        SESSIONS.clear();
        FALL_PROTECT.clear();
    }

    /** Runs once per server tick (see CommonEvents). */
    public static void tick(MinecraftServer server) {
        tickFallProtection(server);
        if (SESSIONS.isEmpty()) {
            return;
        }
        for (Session session : new ArrayList<>(SESSIONS.values())) {
            if (!SESSIONS.containsKey(session.caster)) {
                continue; // cancelled meanwhile by an event
            }
            try {
                tickSession(server, session);
            } catch (RuntimeException ex) {
                PainOrigin.LOGGER.error("Chibaku Tensei failed and was cancelled", ex);
                cancel(session, "invalid");
            }
        }
    }

    public static DamageSource damageSource(ServerLevel level, Entity attacker, String name) {
        try {
            Registry<DamageType> registry = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
            Holder<DamageType> holder = registry.getHolderOrThrow(ResourceKey.create(Registries.DAMAGE_TYPE, PainOrigin.id(name)));
            return new DamageSource(holder, attacker, attacker);
        } catch (RuntimeException ex) {
            // the data pack of this mod is missing: fall back to plain magic damage
            return level.damageSources().indirectMagic(attacker, attacker);
        }
    }

    // ------------------------------------------------------------------------------------------
    // per tick
    // ------------------------------------------------------------------------------------------

    private static void tickSession(MinecraftServer server, Session s) {
        ServerLevel level = server.getLevel(s.dimension);
        if (level == null) {
            cancel(s, "invalid");
            return;
        }
        ServerPlayer caster = server.getPlayerList().getPlayer(s.caster);
        if (caster == null) {
            cancel(s, "logout");
            return;
        }
        if (!caster.isAlive()) {
            cancel(s, "death");
            return;
        }
        if (caster.level().dimension() != s.dimension) {
            cancel(s, "dimension");
            return;
        }
        double maxDistance = PainConfig.CHIBAKU_INTERRUPT_DISTANCE.get();
        if (caster.position().distanceToSqr(s.anchor) > maxDistance * maxDistance) {
            cancel(s, "distance");
            return;
        }

        s.tick++;
        int t = s.tick;
        Phase phase = phaseAt(s, t);
        if (phase != s.phase) {
            s.phase = phase;
            enterPhase(level, caster, s, phase);
        }

        switch (phase) {
            case ACTIVATION -> {
                if (t % 2 == 0) {
                    Fx.vortex(level, caster.position().add(0.0, 1.0, 0.0), 4.0, Fx.scaled(2.0));
                }
            }
            case CORE -> coreVisual(level, s, t, FxStyle.NORMAL);
            case FIELD -> {
                coreVisual(level, s, t, FxStyle.NORMAL);
                double radius = fieldRadiusNow(s, t);
                if (t % 10 == 0) {
                    Fx.pulse(level, s.anchor, radius);
                }
                if (t % 2 == 0) {
                    applyPull(level, caster, s, radius, 1.0, false);
                }
            }
            case DEBRIS -> {
                coreVisual(level, s, t, FxStyle.NORMAL);
                spawnDebris(level, s);
                if (t % 20 == 0) {
                    playSound(level, s.core, ModSounds.CHIBAKU_DEBRIS.get(), 3.0F, 0.9F);
                }
                if (t % 2 == 0) {
                    applyPull(level, caster, s, s.fieldRadius, 1.4, t >= s.liftStart);
                }
            }
            case FORMATION -> {
                coreVisual(level, s, t, FxStyle.FIELD);
                spawnDebris(level, s);
                if (t % 30 == 0) {
                    playSound(level, s.core, ModSounds.CHIBAKU_CORE.get(), 4.0F, 0.6F);
                }
                if (t % 2 == 0) {
                    applyPull(level, caster, s, s.fieldRadius, 1.8, t >= s.liftStart);
                }
            }
            case FINAL -> finish(level, caster, s);
        }
    }

    private static int at(Session s, double fraction) {
        return (int) Math.round(s.duration * fraction);
    }

    private static Phase phaseAt(Session s, int t) {
        if (t >= s.duration) {
            return Phase.FINAL;
        }
        if (t < at(s, 0.10)) {
            return Phase.ACTIVATION;
        }
        if (t < at(s, 0.25)) {
            return Phase.CORE;
        }
        if (t < at(s, 0.55)) {
            return Phase.FIELD;
        }
        if (t < at(s, 0.80)) {
            return Phase.DEBRIS;
        }
        return Phase.FORMATION;
    }

    private static void enterPhase(ServerLevel level, ServerPlayer caster, Session s, Phase phase) {
        caster.displayClientMessage(Component.translatable("painorigin.chibaku.phase." + phase.key), true);
        switch (phase) {
            case CORE -> playSound(level, s.core, ModSounds.CHIBAKU_CORE.get(), 5.0F, 0.8F);
            case FIELD -> playSound(level, s.anchor, ModSounds.CHIBAKU_CORE.get(), 4.0F, 0.6F);
            case DEBRIS -> {
                planSources(level, caster, s);
                playSound(level, s.core, ModSounds.CHIBAKU_DEBRIS.get(), 5.0F, 0.8F);
            }
            case FORMATION -> {
                Fx.burst(level, s.core, 6.0, 14.0, FxStyle.FIELD);
                playSound(level, s.core, ModSounds.CHIBAKU_CORE.get(), 6.0F, 0.5F);
            }
            default -> {
            }
        }
    }

    private static double progress(int t, int from, int to) {
        return Mth.clamp((t - from) / (double) Math.max(1, to - from), 0.0, 1.0);
    }

    private static double easeOut(double f) {
        return 1.0 - (1.0 - f) * (1.0 - f);
    }

    private static double fieldRadiusNow(Session s, int t) {
        return s.fieldRadius * (0.4 + 0.6 * progress(t, at(s, 0.25), at(s, 0.55)));
    }

    private static void coreVisual(ServerLevel level, Session s, int t, int style) {
        if (t % 4 != 0) {
            return;
        }
        int from = at(s, 0.10);
        double maxRadius = Mth.clamp(s.fieldRadius * 0.18, 2.5, 7.0);
        double r0 = 0.5 + (maxRadius - 0.5) * easeOut(progress(t, from, s.duration));
        double r1 = 0.5 + (maxRadius - 0.5) * easeOut(progress(t + 4, from, s.duration));
        Fx.chibakuCore(level, s.core, r0, (r1 - r0) / 4.0, style);
    }

    // ------------------------------------------------------------------------------------------
    // gravity
    // ------------------------------------------------------------------------------------------

    private static boolean isValidTarget(LivingEntity e, ServerPlayer caster, boolean players) {
        if (e == caster || !e.isAlive() || e.isSpectator() || e instanceof ArmorStand) {
            return false;
        }
        if (e.getType().is(IMMUNE)) {
            return false;
        }
        if (e instanceof Player other) {
            if (!players || other.isCreative() || !caster.canHarmPlayer(other)) {
                return false;
            }
        }
        if (e instanceof TamableAnimal pet && pet.isOwnedBy(caster)) {
            return false;
        }
        return true;
    }

    private static double horizontalDistSqr(Entity e, Vec3 anchor) {
        double dx = e.getX() - anchor.x;
        double dz = e.getZ() - anchor.z;
        return dx * dx + dz * dz;
    }

    private static List<LivingEntity> collectTargets(ServerLevel level, ServerPlayer caster, Session s, double radius) {
        AABB box = new AABB(s.anchor.x - radius, s.anchor.y - 4.0, s.anchor.z - radius,
                s.anchor.x + radius, s.core.y + 4.0, s.anchor.z + radius);
        boolean players = PainConfig.CHIBAKU_AFFECT_PLAYERS.get();
        List<LivingEntity> list = level.getEntitiesOfClass(LivingEntity.class, box, e -> isValidTarget(e, caster, players));
        double radius2 = radius * radius;
        list.removeIf(e -> horizontalDistSqr(e, s.anchor) > radius2);
        list.sort(Comparator.comparingDouble(e -> horizontalDistSqr(e, s.anchor)));
        int max = PainConfig.CHIBAKU_MAX_ENTITIES.get();
        if (list.size() > max) {
            return new ArrayList<>(list.subList(0, max));
        }
        return list;
    }

    /**
     * @param toCore false = only drag creatures horizontally toward the axis (they stay on the ground);
     *               true  = lift them toward the core (limited to maxAirborneTicks per creature)
     */
    private static void applyPull(ServerLevel level, ServerPlayer caster, Session s, double radius,
                                  double strength, boolean toCore) {
        double pull = PainConfig.CHIBAKU_PULL.get() * strength;
        for (LivingEntity e : collectTargets(level, caster, s, radius)) {
            s.touched.add(e.getUUID());
            Vec3 center = e.position().add(0.0, e.getBbHeight() * 0.5, 0.0);
            Vec3 v = e.getDeltaMovement();
            if (toCore) {
                int air = s.airborne.getOrDefault(e.getUUID(), 0);
                air = e.onGround() ? 0 : air + 2;
                s.airborne.put(e.getUUID(), air);
                if (air <= s.maxAirborne) {
                    Vec3 d = s.core.subtract(center);
                    double len = d.length();
                    if (len > 2.5) {
                        double speed = Math.min(0.5, pull * (0.6 + len * 0.04));
                        v = v.scale(0.5).add(d.scale(speed / len));
                    } else {
                        v = v.scale(0.3).add(d.scale(0.08));
                    }
                }
            } else {
                Vec3 d = new Vec3(s.anchor.x - center.x, 0.0, s.anchor.z - center.z);
                double len = d.length();
                if (len > 1.5) {
                    double speed = Math.min(0.5, pull * (0.4 + 0.6 * (len / radius)));
                    Vec3 dir = d.scale(1.0 / len);
                    v = new Vec3(v.x * 0.6 + dir.x * speed, v.y, v.z * 0.6 + dir.z * speed);
                }
            }
            e.setDeltaMovement(v);
            e.hurtMarked = true;
            e.fallDistance = 0.0F;
        }
    }

    // ------------------------------------------------------------------------------------------
    // debris / blocks
    // ------------------------------------------------------------------------------------------

    /**
     * Picks up to maxBlocks ground blocks around the caster. Simulated mode: they are only the starting
     * points of debris particles. Real mode: they have already passed BlockSafety and are removed in finish().
     */
    private static void planSources(ServerLevel level, ServerPlayer caster, Session s) {
        int max = PainConfig.CHIBAKU_MAX_BLOCKS.get();
        if (max <= 0) {
            return;
        }
        boolean real = PainConfig.CHIBAKU_REAL_BLOCKS.get();
        BlockSafety safety = real ? new BlockSafety(level, caster) : null;
        double radius = Math.min(PainConfig.CHIBAKU_BLOCK_RADIUS.get(), s.fieldRadius);
        RandomSource rnd = level.getRandom();
        Set<BlockPos> chosen = new LinkedHashSet<>();
        int attempts = max * 6;
        for (int i = 0; i < attempts && chosen.size() < max; i++) {
            double angle = rnd.nextDouble() * Math.PI * 2.0;
            double r = radius * Math.sqrt(rnd.nextDouble());
            int x = Mth.floor(s.anchor.x + Math.cos(angle) * r);
            int z = Mth.floor(s.anchor.z + Math.sin(angle) * r);
            BlockPos column = new BlockPos(x, Mth.floor(s.anchor.y), z);
            if (!level.hasChunkAt(column)) {
                continue;
            }
            BlockPos surface = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, column).below();
            if (Math.abs(surface.getY() - s.anchor.y) > 6.0) {
                continue; // cliff / cave / hole: keep the pieces near the caster's level
            }
            if (real) {
                if (!safety.canConsume(surface)) {
                    continue;
                }
            } else if (level.getBlockState(surface).isAir()) {
                continue;
            }
            chosen.add(surface);
        }
        s.sources.addAll(chosen);
    }

    private static void spawnDebris(ServerLevel level, Session s) {
        if (s.nextSource >= s.sources.size()) {
            return;
        }
        int window = Math.max(1, (int) Math.round(s.duration * 0.35));
        int perTick = Math.max(1, (int) Math.ceil(s.sources.size() / (double) window));
        for (int i = 0; i < perTick && s.nextSource < s.sources.size(); i++) {
            BlockPos pos = s.sources.get(s.nextSource++);
            if (Fx.scaled(1.0) > 0) {
                Fx.debris(level, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, s.core);
            }
        }
    }

    private static void consumeBlocks(ServerLevel level, ServerPlayer caster, Session s) {
        int max = PainConfig.CHIBAKU_MAX_BLOCKS.get();
        BlockSafety safety = new BlockSafety(level, caster);
        int removed = 0;
        for (BlockPos pos : s.sources) {
            if (removed >= max) {
                break;
            }
            if (!safety.canConsume(pos)) {
                continue; // changed since planning, or no longer allowed
            }
            BlockState state = level.getBlockState(pos);
            level.levelEvent(2001, pos, Block.getId(state)); // 2001 = block-break particles + sound
            level.removeBlock(pos, false);
            removed++;
        }
        PainOrigin.LOGGER.info("Chibaku Tensei of {} removed {} block(s)", caster.getName().getString(), removed);
    }

    // ------------------------------------------------------------------------------------------
    // final collapse / cancel
    // ------------------------------------------------------------------------------------------

    private static void finish(ServerLevel level, ServerPlayer caster, Session s) {
        SESSIONS.remove(s.caster);
        Fx.chibakuCollapse(level, s.anchor, s.core, s.fieldRadius);
        playSound(level, s.core, ModSounds.CHIBAKU_COLLAPSE.get(), 8.0F, 0.9F);

        DamageSource source = damageSource(level, caster, "chibaku_tensei");
        float damage = PainConfig.CHIBAKU_DAMAGE.get().floatValue();
        double knockback = PainConfig.CHIBAKU_KNOCKBACK.get();
        for (LivingEntity e : collectTargets(level, caster, s, s.fieldRadius)) {
            double dx = e.getX() - s.anchor.x;
            double dz = e.getZ() - s.anchor.z;
            double len = Math.sqrt(dx * dx + dz * dz);
            double nx = len > 1.0E-3 ? dx / len : 1.0;
            double nz = len > 1.0E-3 ? dz / len : 0.0;
            e.fallDistance = 0.0F;
            if (damage > 0.0F) {
                e.hurt(source, damage);
            }
            e.setDeltaMovement(nx * knockback, 0.35, nz * knockback);
            e.hurtMarked = true;
            protectFall(level, e);
        }
        for (UUID id : s.touched) {
            Entity e = level.getEntity(id);
            if (e != null) {
                protectFall(level, e);
            }
        }
        if (PainConfig.CHIBAKU_REAL_BLOCKS.get()) {
            consumeBlocks(level, caster, s);
        }
    }

    private static void cancel(Session s, String reason) {
        SESSIONS.remove(s.caster);
        ServerLevel level = s.server.getLevel(s.dimension);
        if (level != null) {
            for (UUID id : s.touched) {
                Entity e = level.getEntity(id);
                if (e != null) {
                    protectFall(level, e);
                }
            }
        }
        ServerPlayer caster = s.server.getPlayerList().getPlayer(s.caster);
        if (caster != null) {
            caster.displayClientMessage(Component.translatable("painorigin.chibaku.cancelled." + reason), false);
        }
        PainOrigin.LOGGER.debug("Chibaku Tensei of {} cancelled: {}", s.caster, reason);
    }

    // ------------------------------------------------------------------------------------------
    // fall protection for released creatures
    // ------------------------------------------------------------------------------------------

    private static void protectFall(ServerLevel level, Entity e) {
        FALL_PROTECT.put(e.getUUID(), new Protect(level.dimension()));
    }

    private static void tickFallProtection(MinecraftServer server) {
        if (FALL_PROTECT.isEmpty()) {
            return;
        }
        Iterator<Map.Entry<UUID, Protect>> it = FALL_PROTECT.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<UUID, Protect> entry = it.next();
            Protect protect = entry.getValue();
            ServerLevel level = server.getLevel(protect.dimension);
            Entity e = level == null ? null : level.getEntity(entry.getKey());
            protect.ticksLeft--;
            if (e == null || !e.isAlive() || protect.ticksLeft <= 0 || (protect.sawAir && e.onGround())) {
                it.remove();
                continue;
            }
            if (!e.onGround()) {
                protect.sawAir = true;
            }
            e.fallDistance = 0.0F;
        }
    }

    private static void playSound(ServerLevel level, Vec3 pos, SoundEvent sound, float volume, float pitch) {
        level.playSound(null, pos.x, pos.y, pos.z, sound, SoundSource.PLAYERS, volume, pitch);
    }
}

package com.painorigin;

import java.util.Collections;
import java.util.List;
import net.minecraftforge.common.ForgeConfigSpec;

/**
 * config/painorigin-common.toml - values for the parts that are Java (not JSON):
 * server-side particle output, the phased Chibaku Tensei and the optional block destruction.
 *
 * <p>The numbers of the data-driven powers (Shinra range / force, Ten'in range / pull, gravity-field
 * size, cooldowns, chakra costs) live in the power JSON files and are changed with a datapack - see
 * the README, section "Where is every adjustable value".
 */
public final class PainConfig {
    public static final ForgeConfigSpec SPEC;

    // [particles]
    public static final ForgeConfigSpec.BooleanValue PARTICLES_ENABLED;
    public static final ForgeConfigSpec.DoubleValue PARTICLE_MULTIPLIER;
    public static final ForgeConfigSpec.BooleanValue PARTICLES_AMBIENT;
    public static final ForgeConfigSpec.DoubleValue PARTICLE_RANGE;
    public static final ForgeConfigSpec.BooleanValue PARTICLES_OVERRIDE_LIMITER;

    // [blocks]  (shared safety rules for every feature that can remove blocks)
    public static final ForgeConfigSpec.BooleanValue BLOCK_RESPECT_PROTECTION;
    public static final ForgeConfigSpec.DoubleValue BLOCK_MAX_HARDNESS;
    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> BLOCK_BLACKLIST;

    // [massive]
    public static final ForgeConfigSpec.BooleanValue MASSIVE_BLOCKS_ENABLED;
    public static final ForgeConfigSpec.IntValue MASSIVE_MAX_BLOCKS;
    public static final ForgeConfigSpec.DoubleValue MASSIVE_BLOCK_RADIUS;

    // [chibaku]
    public static final ForgeConfigSpec.BooleanValue CHIBAKU_ENABLED;
    public static final ForgeConfigSpec.IntValue CHIBAKU_DURATION;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_FIELD_RADIUS;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_CORE_HEIGHT;
    public static final ForgeConfigSpec.IntValue CHIBAKU_MAX_BLOCKS;
    public static final ForgeConfigSpec.BooleanValue CHIBAKU_REAL_BLOCKS;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_BLOCK_RADIUS;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_DAMAGE;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_KNOCKBACK;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_PULL;
    public static final ForgeConfigSpec.BooleanValue CHIBAKU_AFFECT_PLAYERS;
    public static final ForgeConfigSpec.IntValue CHIBAKU_MAX_ENTITIES;
    public static final ForgeConfigSpec.IntValue CHIBAKU_MAX_AIRBORNE;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_INTERRUPT_DISTANCE;
    public static final ForgeConfigSpec.DoubleValue CHIBAKU_INTERRUPT_DAMAGE;
    public static final ForgeConfigSpec.IntValue CHIBAKU_MAX_SESSIONS;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();

        b.comment("Particles sent by the SERVER to nearby players. Every player can additionally",
                "reduce or disable them for himself in painorigin-client.toml.").push("particles");
        PARTICLES_ENABLED = b
                .comment("false = the server never sends this mod's particles (powers still work).")
                .define("enabled", true);
        PARTICLE_MULTIPLIER = b
                .comment("Multiplier for the NUMBER of decorative particles (energy streaks, vortex, debris pieces).",
                        "0 = only the main wave / burst / core sprites, 1 = default, 4 = four times as many.")
                .defineInRange("countMultiplier", 1.0, 0.0, 4.0);
        PARTICLES_AMBIENT = b
                .comment("The faint Rinnegan energy that drifts around every Deva Path player.")
                .define("ambientAura", true);
        PARTICLE_RANGE = b
                .comment("Players farther than this many blocks from an effect do not receive its particles.")
                .defineInRange("range", 96.0, 8.0, 512.0);
        PARTICLES_OVERRIDE_LIMITER = b
                .comment("true = show the particles even to players whose vanilla 'Particles' video setting is",
                        "Decreased/Minimal (otherwise vanilla randomly drops some of them / hides all).",
                        "Those players can still switch them off with painorigin-client.toml.")
                .define("overrideVanillaLimit", true);
        b.pop();

        b.comment("Safety rules shared by every feature that can remove blocks (Massive Shinra Tensei",
                "block destruction and the experimental real-block mode of Chibaku Tensei).").push("blocks");
        BLOCK_RESPECT_PROTECTION = b
                .comment("true = before removing a block a Forge BlockEvent.BreakEvent is posted for the caster, so",
                        "claim / protection mods that cancel it are respected. Also requires the caster to be",
                        "allowed to build (not adventure / spectator). Vanilla spawn protection is NOT checked.")
                .define("respectProtection", true);
        BLOCK_MAX_HARDNESS = b
                .comment("Blocks harder than this are never removed (stone 1.5, iron block 5, obsidian 50).",
                        "Unbreakable blocks (bedrock, barrier, command blocks...) are never removed regardless.")
                .defineInRange("maxHardness", 10.0, 0.0, 100.0);
        BLOCK_BLACKLIST = b
                .comment("Extra blocks that are never removed. Block ids ('minecraft:obsidian') or tags ('#forge:ores').",
                        "The tag #painorigin:chibaku_protected is always applied (bedrock, portals, spawners...).")
                .defineListAllowEmpty("blacklist", Collections.<String>emptyList(), o -> o instanceof String);
        b.pop();

        b.comment("Massive Shinra Tensei. The push / damage itself is JSON; this is the OPTIONAL crater.").push("massive");
        MASSIVE_BLOCKS_ENABLED = b
                .comment("false (default) = Massive Shinra Tensei destroys NO blocks.",
                        "true = it removes up to maxBlocks of the nearest blocks (no item drops).")
                .define("blockDestruction", false);
        MASSIVE_MAX_BLOCKS = b
                .comment("Hard cap on the number of blocks removed per use.")
                .defineInRange("maxBlocks", 120, 0, 1000);
        MASSIVE_BLOCK_RADIUS = b
                .comment("Blocks farther than this from the caster are never touched (the push radius is larger).")
                .defineInRange("blockRadius", 6.0, 1.0, 16.0);
        b.pop();

        b.comment("Chibaku Tensei: phased technique run by the server (activation, core, gravity field,",
                "debris attraction, formation, final collapse).").push("chibaku");
        CHIBAKU_ENABLED = b
                .comment("false = the technique does nothing (the chakra cost is still paid by the JSON power).")
                .define("enabled", true);
        CHIBAKU_DURATION = b
                .comment("Total duration in ticks (20 ticks = 1 second). Phases are fixed fractions of it:",
                        "activation 10%, core 15%, gravity field 30%, debris 25%, formation 20%, then the final collapse.")
                .defineInRange("durationTicks", 240, 100, 1200);
        CHIBAKU_FIELD_RADIUS = b
                .comment("Radius (blocks) of the gravity field that pulls creatures and of the final collapse.")
                .defineInRange("fieldRadius", 20.0, 6.0, 48.0);
        CHIBAKU_CORE_HEIGHT = b
                .comment("Height (blocks) above the caster at which the core hangs (lowered under low ceilings / the build limit).")
                .defineInRange("coreHeight", 14.0, 6.0, 40.0);
        CHIBAKU_MAX_BLOCKS = b
                .comment("Maximum number of terrain blocks the technique uses.",
                        "Default (realBlocks=false): that many SIMULATED debris pieces fly into the core - nothing is removed.",
                        "With realBlocks=true: that many real blocks are removed at the final collapse.")
                .defineInRange("maxBlocks", 64, 0, 512);
        CHIBAKU_REAL_BLOCKS = b
                .comment("EXPERIMENTAL, default false. true = the blocks picked for the debris are REALLY removed",
                        "(permanently, no drops) at the final collapse, subject to the [blocks] safety rules.",
                        "Nothing is removed if the technique is cancelled before the collapse.")
                .define("realBlocks", false);
        CHIBAKU_BLOCK_RADIUS = b
                .comment("Debris / removed blocks are taken from the ground within this radius of the caster.")
                .defineInRange("blockRadius", 8.0, 2.0, 24.0);
        CHIBAKU_DAMAGE = b
                .comment("Damage dealt by the final collapse to every captured creature (2 = one heart).",
                        "It uses the damage type painorigin:chibaku_tensei, which bypasses armor.")
                .defineInRange("damage", 16.0, 0.0, 200.0);
        CHIBAKU_KNOCKBACK = b
                .comment("Horizontal outward push at the final collapse.")
                .defineInRange("knockback", 1.4, 0.0, 5.0);
        CHIBAKU_PULL = b
                .comment("Strength of the gravity pull (blocks per tick of added speed).")
                .defineInRange("pullStrength", 0.22, 0.02, 1.5);
        CHIBAKU_AFFECT_PLAYERS = b
                .comment("false = only mobs are pulled / damaged. Creative and spectator players and players that the",
                        "caster may not harm (pvp=false) are always skipped; so are the caster, his pets, armor stands",
                        "and the bosses in #painorigin:chibaku_immune.")
                .define("affectPlayers", true);
        CHIBAKU_MAX_ENTITIES = b
                .comment("At most this many creatures (nearest to the axis first) are affected.")
                .defineInRange("maxEntities", 48, 1, 256);
        CHIBAKU_MAX_AIRBORNE = b
                .comment("A creature is lifted for at most this many ticks; afterwards it is released. Keep this below 80:",
                        "vanilla kicks players that 'float' for more than 80 ticks when allow-flight=false.")
                .defineInRange("maxAirborneTicks", 60, 20, 70);
        CHIBAKU_INTERRUPT_DISTANCE = b
                .comment("The technique is cancelled if the caster moves farther than this from where he started.")
                .defineInRange("interruptDistance", 6.0, 2.0, 32.0);
        CHIBAKU_INTERRUPT_DAMAGE = b
                .comment("The technique is cancelled if the caster takes a single hit of at least this much damage",
                        "(after armor). 0 = damage never interrupts. Death, logout and changing dimension always cancel.")
                .defineInRange("interruptDamage", 3.0, 0.0, 100.0);
        CHIBAKU_MAX_SESSIONS = b
                .comment("Maximum number of Chibaku Tensei running at the same time on the whole server.")
                .defineInRange("maxSessions", 4, 1, 32);
        b.pop();

        SPEC = b.build();
    }

    private PainConfig() {}
}

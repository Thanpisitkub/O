package com.painorigin;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.registries.RegistryObject;

/**
 * {@code /painorigin ...} (permission level 2). These sub-commands are the bridge between the JSON powers
 * and the Java add-on: the powers call them with Apoli's {@code execute_command} action, which runs them
 * as the player at the player's position (or, for the Bansho Ten'in ray, at each step of the ray).
 *
 * <pre>
 *  /painorigin fx shinra_tensei &lt;radius&gt;      shockwave particles
 *  /painorigin fx shinra_massive &lt;radius&gt;     massive shockwave particles
 *  /painorigin fx charge [ticks]              Massive Shinra Tensei charge-up vortex
 *  /painorigin fx bansho_trail                one pull-trail particle at the executing position
 *  /painorigin fx bansho_hit                  flash on the executing entity (the grabbed creature)
 *  /painorigin fx defense                     Universal Defense flash
 *  /painorigin fx rinnegan_ambient            faint ambient energy
 *  /painorigin chibaku start|cancel|status    phased Chibaku Tensei
 *  /painorigin massive_blocks &lt;radius&gt;        optional crater of Massive Shinra Tensei (config, default off)
 *  /painorigin test                           installation self-test
 * </pre>
 */
public final class PainCommands {
    /** Power files that the data pack must contain (checked by /painorigin test). */
    private static final String[] POWER_FILES = {
            "chakra", "chakra_regen", "shinra_tensei", "shinra_tensei_massive", "bansho_tenin", "chibaku_tensei",
            "universal_defense", "defense_charges", "defense_regen", "rinnegan_gravity_field", "rinnegan_aura",
            "gravity_affinity", "frail_vessel", "notice_primary", "notice_secondary", "notice_target", "onboarding"
    };

    private PainCommands() {}

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("painorigin")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("fx")
                        .then(Commands.literal("shinra_tensei")
                                .then(Commands.argument("radius", DoubleArgumentType.doubleArg(1.0, 64.0))
                                        .executes(ctx -> shinra(ctx.getSource(), DoubleArgumentType.getDouble(ctx, "radius"), false))))
                        .then(Commands.literal("shinra_massive")
                                .then(Commands.argument("radius", DoubleArgumentType.doubleArg(1.0, 64.0))
                                        .executes(ctx -> shinra(ctx.getSource(), DoubleArgumentType.getDouble(ctx, "radius"), true))))
                        .then(Commands.literal("charge")
                                .executes(ctx -> charge(ctx.getSource(), 30))
                                .then(Commands.argument("ticks", IntegerArgumentType.integer(5, 200))
                                        .executes(ctx -> charge(ctx.getSource(), IntegerArgumentType.getInteger(ctx, "ticks")))))
                        .then(Commands.literal("bansho_trail").executes(ctx -> banshoTrail(ctx.getSource())))
                        .then(Commands.literal("bansho_hit").executes(ctx -> banshoHit(ctx.getSource())))
                        .then(Commands.literal("defense").executes(ctx -> defense(ctx.getSource())))
                        .then(Commands.literal("rinnegan_ambient").executes(ctx -> ambient(ctx.getSource()))))
                .then(Commands.literal("chibaku")
                        .then(Commands.literal("start").executes(ctx -> chibakuStart(ctx.getSource())))
                        .then(Commands.literal("cancel").executes(ctx -> chibakuCancel(ctx.getSource())))
                        .then(Commands.literal("status").executes(ctx -> chibakuStatus(ctx.getSource()))))
                .then(Commands.literal("massive_blocks")
                        .then(Commands.argument("radius", DoubleArgumentType.doubleArg(1.0, 64.0))
                                .executes(ctx -> massiveBlocks(ctx.getSource(), DoubleArgumentType.getDouble(ctx, "radius")))))
                .then(Commands.literal("test").executes(ctx -> selfTest(ctx.getSource()))));
    }

    // ------------------------------------------------------------------------------------------
    // fx
    // ------------------------------------------------------------------------------------------

    private static int shinra(CommandSourceStack source, double radius, boolean massive) {
        Fx.shinra(source.getLevel(), source.getPosition(), radius, massive);
        return 1;
    }

    private static int charge(CommandSourceStack source, int ticks) {
        if (source.getEntity() instanceof ServerPlayer player) {
            Fx.startCharge(player, ticks);
            return 1;
        }
        return 0;
    }

    private static int banshoTrail(CommandSourceStack source) {
        Entity caster = source.getEntity();
        if (caster == null) {
            return 0;
        }
        Fx.banshoTrail(source.getLevel(), source.getPosition(), caster);
        return 1;
    }

    private static int banshoHit(CommandSourceStack source) {
        Entity target = source.getEntity();
        if (target == null) {
            return 0;
        }
        Fx.banshoHit(source.getLevel(), target);
        return 1;
    }

    private static int defense(CommandSourceStack source) {
        Entity entity = source.getEntity();
        if (entity == null) {
            return 0;
        }
        Fx.defense(source.getLevel(), entity);
        return 1;
    }

    private static int ambient(CommandSourceStack source) {
        Entity entity = source.getEntity();
        if (entity == null) {
            return 0;
        }
        Fx.ambient(source.getLevel(), entity);
        return 1;
    }

    // ------------------------------------------------------------------------------------------
    // chibaku / massive blocks
    // ------------------------------------------------------------------------------------------

    private static int chibakuStart(CommandSourceStack source) {
        if (!(source.getEntity() instanceof ServerPlayer player)) {
            source.sendFailure(Component.translatable("painorigin.command.not_a_player"));
            return 0;
        }
        return ChibakuManager.start(player) ? 1 : 0;
    }

    private static int chibakuCancel(CommandSourceStack source) {
        if (!(source.getEntity() instanceof ServerPlayer player)) {
            source.sendFailure(Component.translatable("painorigin.command.not_a_player"));
            return 0;
        }
        if (ChibakuManager.cancelFor(player.getUUID(), "command")) {
            return 1;
        }
        source.sendFailure(Component.translatable("painorigin.command.chibaku.none"));
        return 0;
    }

    private static int chibakuStatus(CommandSourceStack source) {
        int count = ChibakuManager.activeCount();
        source.sendSuccess(() -> Component.translatable("painorigin.command.chibaku.status", count), false);
        return count;
    }

    private static int massiveBlocks(CommandSourceStack source, double radius) {
        if (!(source.getEntity() instanceof ServerPlayer player)) {
            source.sendFailure(Component.translatable("painorigin.command.not_a_player"));
            return 0;
        }
        int removed = MassiveBlocks.run(player, radius);
        if (removed < 0) {
            source.sendSuccess(() -> Component.translatable("painorigin.command.massive_blocks.disabled"), false);
            return 0;
        }
        source.sendSuccess(() -> Component.translatable("painorigin.command.massive_blocks", removed), false);
        return removed;
    }

    // ------------------------------------------------------------------------------------------
    // self test
    // ------------------------------------------------------------------------------------------

    /** Checks that everything this mod registers or ships is actually present in the running game. */
    private static int selfTest(CommandSourceStack source) {
        List<String> failed = new ArrayList<>();
        int ok = 0;

        for (RegistryObject<SimpleParticleType> particle : ModParticles.ALL) {
            if (particle.isPresent()) {
                ok++;
            } else {
                failed.add("particle " + particle.getId());
            }
        }
        for (RegistryObject<SoundEvent> sound : ModSounds.ALL) {
            if (sound.isPresent()) {
                ok++;
            } else {
                failed.add("sound " + sound.getId());
            }
        }

        Registry<DamageType> damageTypes = source.getLevel().registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
        for (String name : new String[] {"shinra_tensei", "chibaku_tensei"}) {
            ResourceLocation id = PainOrigin.id(name);
            if (damageTypes.containsKey(id)) {
                ok++;
            } else {
                failed.add("damage_type " + id);
            }
        }

        if (BuiltInRegistries.BLOCK.getTag(BlockSafety.PROTECTED).isPresent()) {
            ok++;
        } else {
            failed.add("block tag #" + BlockSafety.PROTECTED.location());
        }
        if (BuiltInRegistries.ENTITY_TYPE.getTag(ChibakuManager.IMMUNE).isPresent()) {
            ok++;
        } else {
            failed.add("entity tag #" + ChibakuManager.IMMUNE.location());
        }

        ResourceManager resources = source.getServer().getResourceManager();
        List<ResourceLocation> files = new ArrayList<>();
        for (String name : POWER_FILES) {
            files.add(PainOrigin.id("powers/" + name + ".json"));
        }
        files.add(PainOrigin.id("origins/deva_path.json"));
        for (ResourceLocation id : files) {
            if (resources.getResource(id).isPresent()) {
                ok++;
            } else {
                failed.add("data file " + id);
            }
        }

        if (failed.isEmpty()) {
            int passed = ok;
            source.sendSuccess(() -> Component.translatable("painorigin.command.test.ok", passed), false);
            return 1;
        }
        source.sendFailure(Component.translatable("painorigin.command.test.fail", String.join(", ", failed)));
        return 0;
    }
}

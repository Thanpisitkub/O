package com.painorigin;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.level.BlockEvent;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * One shared answer to "may this technique remove this block?". Used by Massive Shinra Tensei's
 * optional crater and by the experimental real-block mode of Chibaku Tensei. A block is refused when
 * ANY of these holds:
 * <ul>
 *   <li>outside the world / world border, or in an unloaded chunk;</li>
 *   <li>air, fluid (or waterlogged), or anything with a block entity (chests, spawners, beacons...);</li>
 *   <li>unbreakable (hardness &lt; 0: bedrock, barrier, command blocks, portal frames...) or harder than
 *       {@code blocks.maxHardness};</li>
 *   <li>in the block tag {@code #painorigin:chibaku_protected} or the config {@code blocks.blacklist};</li>
 *   <li>the caster is a spectator / not allowed to build, or a {@link BlockEvent.BreakEvent} posted for the
 *       caster is cancelled (claim and protection mods) - the answer is cached per chunk so a claimed
 *       chunk produces one event, not hundreds.</li>
 * </ul>
 * Vanilla spawn protection is not checked.
 */
public final class BlockSafety {
    /** Never-remove list shipped in the data pack (data/painorigin/tags/blocks/chibaku_protected.json). */
    public static final TagKey<Block> PROTECTED = TagKey.create(Registries.BLOCK, PainOrigin.id("chibaku_protected"));

    private final ServerLevel level;
    private final ServerPlayer player;
    private final double maxHardness;
    private final boolean respectProtection;
    private final Set<String> blacklistIds = new HashSet<>();
    private final List<TagKey<Block>> blacklistTags = new ArrayList<>();
    private final Set<Long> deniedChunks = new HashSet<>();

    public BlockSafety(ServerLevel level, ServerPlayer player) {
        this.level = level;
        this.player = player;
        this.maxHardness = PainConfig.BLOCK_MAX_HARDNESS.get();
        this.respectProtection = PainConfig.BLOCK_RESPECT_PROTECTION.get();
        for (String raw : PainConfig.BLOCK_BLACKLIST.get()) {
            String entry = raw.trim();
            if (entry.isEmpty()) {
                continue;
            }
            boolean isTag = entry.startsWith("#");
            ResourceLocation id = ResourceLocation.tryParse(isTag ? entry.substring(1) : entry);
            if (id == null) {
                PainOrigin.LOGGER.warn("Ignoring invalid entry '{}' in painorigin-common.toml [blocks] blacklist", raw);
            } else if (isTag) {
                blacklistTags.add(TagKey.create(Registries.BLOCK, id));
            } else {
                blacklistIds.add(id.toString());
            }
        }
    }

    public boolean canConsume(BlockPos pos) {
        if (!level.isInWorldBounds(pos) || !level.hasChunkAt(pos)) {
            return false;
        }
        if (!level.getWorldBorder().isWithinBounds(pos)) {
            return false;
        }
        BlockState state = level.getBlockState(pos);
        if (state.isAir()) {
            return false;
        }
        float hardness = state.getDestroySpeed(level, pos);
        if (hardness < 0.0F || hardness > maxHardness) {
            return false;
        }
        if (state.hasBlockEntity() || !state.getFluidState().isEmpty()) {
            return false;
        }
        if (state.is(PROTECTED)) {
            return false;
        }
        ResourceLocation key = ForgeRegistries.BLOCKS.getKey(state.getBlock());
        if (key != null && blacklistIds.contains(key.toString())) {
            return false;
        }
        for (TagKey<Block> tag : blacklistTags) {
            if (state.is(tag)) {
                return false;
            }
        }
        if (player != null) {
            if (player.isSpectator() || !player.mayBuild()) {
                return false;
            }
            if (respectProtection) {
                long chunk = ChunkPos.asLong(pos.getX() >> 4, pos.getZ() >> 4);
                if (deniedChunks.contains(chunk)) {
                    return false;
                }
                BlockEvent.BreakEvent event = new BlockEvent.BreakEvent(level, pos, state, player);
                if (MinecraftForge.EVENT_BUS.post(event)) {
                    deniedChunks.add(chunk);
                    return false;
                }
            }
        }
        return true;
    }
}

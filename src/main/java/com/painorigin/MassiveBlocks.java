package com.painorigin;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Optional crater of Massive Shinra Tensei ({@code /painorigin massive_blocks <radius>}, run by the JSON
 * power right after the push). OFF by default ({@code massive.blockDestruction = false}).
 *
 * <p>When enabled it removes at most {@code massive.maxBlocks} blocks, nearest first, within
 * {@code min(radius, massive.blockRadius)} of the caster, without item drops. Every block must pass
 * {@link BlockSafety}. The ground directly under the caster is never touched.
 */
public final class MassiveBlocks {
    private MassiveBlocks() {}

    /** @return the number of blocks removed, or -1 when block destruction is disabled in the config. */
    public static int run(ServerPlayer player, double radiusArgument) {
        if (!PainConfig.MASSIVE_BLOCKS_ENABLED.get()) {
            return -1;
        }
        int max = PainConfig.MASSIVE_MAX_BLOCKS.get();
        if (max <= 0) {
            return 0;
        }
        ServerLevel level = (ServerLevel) player.level();
        double radius = Math.min(radiusArgument, PainConfig.MASSIVE_BLOCK_RADIUS.get());
        double radius2 = radius * radius;
        int reach = (int) Math.ceil(radius);

        Vec3 center = player.position().add(0.0, 1.0, 0.0);
        BlockPos origin = BlockPos.containing(center);
        int feetY = Mth.floor(player.getY());

        List<BlockPos> candidates = new ArrayList<>();
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int dx = -reach; dx <= reach; dx++) {
            for (int dy = -reach; dy <= reach; dy++) {
                for (int dz = -reach; dz <= reach; dz++) {
                    if (dx * dx + dy * dy + dz * dz > radius2) {
                        continue;
                    }
                    int x = origin.getX() + dx;
                    int y = origin.getY() + dy;
                    int z = origin.getZ() + dz;
                    boolean underCaster = y < feetY
                            && Math.abs(x + 0.5 - player.getX()) < 1.6
                            && Math.abs(z + 0.5 - player.getZ()) < 1.6;
                    if (underCaster) {
                        continue;
                    }
                    cursor.set(x, y, z);
                    if (!level.getBlockState(cursor).isAir()) {
                        candidates.add(cursor.immutable());
                    }
                }
            }
        }
        candidates.sort(Comparator.comparingDouble(pos -> pos.distSqr(origin)));

        BlockSafety safety = new BlockSafety(level, player);
        int removed = 0;
        for (BlockPos pos : candidates) {
            if (removed >= max) {
                break;
            }
            if (safety.canConsume(pos)) {
                level.destroyBlock(pos, false, player);
                removed++;
            }
        }
        return removed;
    }
}

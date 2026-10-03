package com.imainjager.forgedascent.smithy;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A Smithy Anvil: opens a 3x3 crafting grid that takes anvil recipes of up to this anvil's tier. Doesn't fall or break down. */
public class SmithyAnvilBlock extends Block {
    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;
    private static final VoxelShape BASE = Block.box(2, 0, 2, 14, 4, 14);
    private static final VoxelShape X_AXIS = Shapes.or(BASE, Block.box(3, 4, 4, 13, 5, 12),
            Block.box(4, 5, 6, 12, 10, 10), Block.box(0, 10, 3, 16, 16, 13));
    private static final VoxelShape Z_AXIS = Shapes.or(BASE, Block.box(4, 4, 3, 12, 5, 13),
            Block.box(6, 5, 4, 10, 10, 12), Block.box(3, 10, 0, 13, 16, 16));

    private final int tier;

    public SmithyAnvilBlock(int tier, Properties properties) {
        super(properties);
        this.tier = tier;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    public int tier() {
        return tier;
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return simpleCodec(p -> new SmithyAnvilBlock(tier, p));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getClockWise());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(FACING).getAxis() == Direction.Axis.X ? X_AXIS : Z_AXIS;
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide()) return InteractionResult.SUCCESS;
        player.openMenu(new SimpleMenuProvider(
                (id, inventory, p) -> new SmithyMenu(id, inventory, ContainerLevelAccess.create(level, pos), tier),
                Component.translatable(getDescriptionId())), buf -> buf.writeVarInt(tier));
        return InteractionResult.CONSUME;
    }
}

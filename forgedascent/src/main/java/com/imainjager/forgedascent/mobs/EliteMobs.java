package com.imainjager.forgedascent.mobs;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.ModRegistries;
import net.minecraft.world.item.Item;
import net.neoforged.neoforge.common.DeferredSpawnEggItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.monster.AbstractSkeleton;
import net.minecraft.world.entity.monster.Spider;
import net.minecraft.world.entity.monster.Witch;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.monster.piglin.Piglin;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.jetbrains.annotations.Nullable;

import java.util.EnumMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Registers the elite mob types: one per (base mob, elite type), e.g. forgedascent:brute_zombie. */
public final class EliteMobs {
    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(Registries.ENTITY_TYPE, ForgedAscent.MOD_ID);

    /** Vanilla mob families that get elite versions, and the vanilla types that convert into them. */
    public enum Base {
        ZOMBIE("zombie", EntityType.ZOMBIE, List.of(EntityType.ZOMBIE, EntityType.HUSK), 0x00AFAF),
        SKELETON("skeleton", EntityType.SKELETON, List.of(EntityType.SKELETON, EntityType.STRAY), 0xC1C1C1),
        SPIDER("spider", EntityType.SPIDER, List.of(EntityType.SPIDER, EntityType.CAVE_SPIDER), 0x342D27),
        WITHER_SKELETON("wither_skeleton", EntityType.WITHER_SKELETON, List.of(EntityType.WITHER_SKELETON), 0x141414),
        PIGLIN("piglin", EntityType.PIGLIN, List.of(EntityType.PIGLIN), 0x995F40),
        WITCH("witch", EntityType.WITCH, List.of(EntityType.WITCH), 0x340000);

        public final String id;
        public final EntityType<?> vanilla;
        public final List<EntityType<?>> convertsFrom;
        public final int eggColor;

        Base(String id, EntityType<?> vanilla, List<EntityType<?>> convertsFrom, int eggColor) {
            this.id = id;
            this.vanilla = vanilla;
            this.convertsFrom = convertsFrom;
            this.eggColor = eggColor;
        }
    }

    private static final Map<Base, Map<EliteType, DeferredHolder<EntityType<?>, ? extends EntityType<? extends Mob>>>> TYPES =
            new EnumMap<>(Base.class);
    private static Map<EntityType<?>, EliteType> eliteByType;
    private static Map<EntityType<?>, Base> baseByVanilla;

    private EliteMobs() {}

    public static void register(IEventBus modBus) {
        for (Base base : Base.values()) {
            Map<EliteType, DeferredHolder<EntityType<?>, ? extends EntityType<? extends Mob>>> byElite = new EnumMap<>(EliteType.class);
            for (EliteType elite : EliteType.values()) {
                String name = elite.id() + "_" + base.id;
                var holder = ENTITY_TYPES.register(name, () -> build(base, name));
                byElite.put(elite, holder);
                ModRegistries.addToTab(ModRegistries.ITEMS.register(name + "_spawn_egg", () -> new DeferredSpawnEggItem(
                        holder, base.eggColor, elite.tint, new Item.Properties())));
            }
            TYPES.put(base, byElite);
        }
        ENTITY_TYPES.register(modBus);
        modBus.addListener(EliteMobs::attributes);
    }

    private static EntityType<? extends Mob> build(Base base, String name) {
        EntityType<?> v = base.vanilla;
        EntityType.Builder<? extends Mob> builder = switch (base) {
            case ZOMBIE -> EntityType.Builder.of(EliteEntities.EliteZombie::new, MobCategory.MONSTER);
            case SKELETON -> EntityType.Builder.of(EliteEntities.EliteSkeleton::new, MobCategory.MONSTER);
            case SPIDER -> EntityType.Builder.of(EliteEntities.EliteSpider::new, MobCategory.MONSTER);
            case WITHER_SKELETON -> EntityType.Builder.of(EliteEntities.EliteWitherSkeleton::new, MobCategory.MONSTER)
                    .fireImmune().immuneTo(Blocks.WITHER_ROSE);
            case PIGLIN -> EntityType.Builder.of(EliteEntities.ElitePiglin::new, MobCategory.MONSTER);
            case WITCH -> EntityType.Builder.of(EliteEntities.EliteWitch::new, MobCategory.MONSTER);
        };
        return builder.sized(v.getWidth(), v.getHeight())
                .eyeHeight(v.getDimensions().eyeHeight())
                .clientTrackingRange(8)
                .build(ForgedAscent.id(name).toString());
    }

    private static void attributes(EntityAttributeCreationEvent event) {
        for (Base base : Base.values()) {
            Supplier<AttributeSupplier.Builder> attrs = switch (base) {
                case ZOMBIE -> Zombie::createAttributes;
                case SKELETON, WITHER_SKELETON -> AbstractSkeleton::createAttributes;
                case SPIDER -> Spider::createAttributes;
                case PIGLIN -> Piglin::createAttributes;
                case WITCH -> Witch::createAttributes;
            };
            for (var holder : TYPES.get(base).values()) {
                event.put(holder.get(), attrs.get().build());
            }
        }
    }

    public static EntityType<? extends Mob> type(Base base, EliteType elite) {
        return TYPES.get(base).get(elite).get();
    }

    public static Map<Base, Map<EliteType, DeferredHolder<EntityType<?>, ? extends EntityType<? extends Mob>>>> all() {
        return TYPES;
    }

    /** The elite type of one of our elite mob types, or null. */
    @Nullable
    public static EliteType eliteOf(EntityType<?> type) {
        if (eliteByType == null) {
            Map<EntityType<?>, EliteType> map = new IdentityHashMap<>();
            TYPES.values().forEach(m -> m.forEach((elite, holder) -> map.put(holder.get(), elite)));
            eliteByType = map;
        }
        return eliteByType.get(type);
    }

    /** Which elite family a vanilla type converts into, or null. */
    @Nullable
    public static Base baseFor(EntityType<?> vanilla) {
        if (baseByVanilla == null) {
            Map<EntityType<?>, Base> map = new IdentityHashMap<>();
            for (Base b : Base.values()) b.convertsFrom.forEach(t -> map.put(t, b));
            baseByVanilla = map;
        }
        return baseByVanilla.get(vanilla);
    }
}

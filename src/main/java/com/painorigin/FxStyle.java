package com.painorigin;

/**
 * "Style" codes carried in the third free parameter of the wave / burst particles. They are
 * compile-time constants shared by the server ({@link Fx}) and the client particle classes, so the
 * client never has to load server classes to read them.
 */
public final class FxStyle {
    /** Shinra Tensei / default look (white-blue). */
    public static final int NORMAL = 0;
    /** Massive Shinra Tensei (violet-white, bigger). */
    public static final int MASSIVE = 1;
    /** Chibaku Tensei gravity-field pulse and formation (violet, dim). */
    public static final int FIELD = 2;
    /** Universal Defense barrier flash (cyan). */
    public static final int DEFENSE = 3;
    /** Bansho Ten'in impact flash (blue-violet). */
    public static final int HIT = 4;
    /** Chibaku Tensei collapse (bright violet-white). */
    public static final int COLLAPSE = 5;

    private FxStyle() {}
}

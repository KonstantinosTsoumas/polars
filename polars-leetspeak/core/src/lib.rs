//! Pure leetspeak transformation, free of any Polars or Python types.
//!
//! The `leetspeak` crate wraps these functions as Polars expressions; nothing
//! here knows that Polars exists.

/// How aggressively to substitute characters.
///
/// Each level is a superset of the one below it, so `Level3` also applies every
/// `Level1` and `Level2` substitution.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Level {
    /// The classic vowel-and-`s`/`t` swaps. Output length always equals input.
    Basic,
    /// Adds the remaining single-character swaps.
    Advanced,
    /// Adds multi-character glyphs, so the output can grow.
    Extreme,
}

impl Level {
    pub fn from_u8(level: u8) -> Option<Self> {
        match level {
            1 => Some(Level::Basic),
            2 => Some(Level::Advanced),
            3 => Some(Level::Extreme),
            _ => None,
        }
    }
}

/// The substitution for `c` at `level`, or `None` to leave the character alone.
fn substitute(c: char, level: Level) -> Option<&'static str> {
    let basic = match c.to_ascii_lowercase() {
        'a' => Some("4"),
        'e' => Some("3"),
        'i' => Some("1"),
        'o' => Some("0"),
        's' => Some("5"),
        't' => Some("7"),
        _ => None,
    };
    if basic.is_some() || level == Level::Basic {
        return basic;
    }

    let advanced = match c.to_ascii_lowercase() {
        'b' => Some("8"),
        'g' => Some("9"),
        'l' => Some("|"),
        'z' => Some("2"),
        _ => None,
    };
    if advanced.is_some() || level == Level::Advanced {
        return advanced;
    }

    match c.to_ascii_lowercase() {
        'w' => Some(r"\/\/"),
        'm' => Some(r"/\/\"),
        'n' => Some(r"/\"),
        'v' => Some(r"\/"),
        'c' => Some("("),
        'd' => Some("|)"),
        _ => None,
    }
}

/// Write the leetspeak form of `value` into `output`.
///
/// `output` is an amortised buffer owned by the caller, so nothing is allocated
/// per row. Characters with no substitution are uppercased unless
/// `preserve_case` is set.
pub fn leetify(value: &str, level: Level, preserve_case: bool, output: &mut String) {
    for c in value.chars() {
        match substitute(c, level) {
            Some(sub) => output.push_str(sub),
            None if preserve_case => output.push(c),
            // `to_uppercase` can yield more than one char (e.g. 'ß' -> "SS").
            None => {
                for upper in c.to_uppercase() {
                    output.push(upper)
                }
            },
        }
    }
}

/// Best-effort inverse of [`leetify`].
///
/// This is lossy by nature: `leetify` maps both `l` and `i` onto digits and
/// discards case, so round-tripping recovers the shape of the word, not the
/// original text. Multi-character glyphs are matched before single characters
/// so that `\/\/` becomes `w` rather than two `v`s.
pub fn unleetify(value: &str, output: &mut String) {
    const GLYPHS: [(&str, char); 6] = [
        (r"/\/\", 'm'),
        (r"\/\/", 'w'),
        (r"/\", 'n'),
        (r"\/", 'v'),
        ("|)", 'd'),
        ("|", 'l'),
    ];

    let mut rest = value;
    'outer: while !rest.is_empty() {
        for (glyph, plain) in GLYPHS {
            if let Some(tail) = rest.strip_prefix(glyph) {
                output.push(plain);
                rest = tail;
                continue 'outer;
            }
        }

        // Not a glyph, so consume exactly one character.
        let c = rest.chars().next().unwrap();
        rest = &rest[c.len_utf8()..];
        let plain = match c {
            '4' => 'a',
            '3' => 'e',
            '1' => 'i',
            '0' => 'o',
            '5' => 's',
            '7' => 't',
            '8' => 'b',
            '9' => 'g',
            '2' => 'z',
            '(' => 'c',
            _ => {
                for lower in c.to_lowercase() {
                    output.push(lower)
                }
                continue;
            },
        };
        output.push(plain)
    }
}

/// Count the characters that `level` would substitute.
pub fn count_substitutions(value: &str, level: Level) -> u32 {
    value
        .chars()
        .filter(|c| substitute(*c, level).is_some())
        .count() as u32
}

/// Used by the `leet_ratio` expression to report substitutions per character.
pub fn substitution_ratio(value: &str, level: Level) -> f64 {
    let total = value.chars().count();
    if total == 0 {
        return 0.0;
    }
    count_substitutions(value, level) as f64 / total as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    fn leet(value: &str, level: Level, preserve_case: bool) -> String {
        let mut out = String::new();
        leetify(value, level, preserve_case, &mut out);
        out
    }

    fn unleet(value: &str) -> String {
        let mut out = String::new();
        unleetify(value, &mut out);
        out
    }

    #[test]
    fn basic_level_substitutes_only_the_classic_set() {
        assert_eq!(leet("polars", Level::Basic, true), "p0l4r5");
        // `b` and `l` belong to the advanced set, so they survive untouched.
        assert_eq!(leet("blaze", Level::Basic, true), "bl4z3");
    }

    #[test]
    fn advanced_level_adds_the_remaining_single_char_swaps() {
        assert_eq!(leet("blaze", Level::Advanced, true), "8|423");
    }

    #[test]
    fn extreme_level_can_grow_the_output() {
        let out = leet("wm", Level::Extreme, true);
        assert_eq!(out, r"\/\//\/\");
        assert!(out.len() > "wm".len());
    }

    #[test]
    fn unmapped_characters_are_uppercased_unless_preserved() {
        assert_eq!(leet("hi there", Level::Basic, false), "H1 7H3R3");
        assert_eq!(leet("hi there", Level::Basic, true), "h1 7h3r3");
    }

    #[test]
    fn substitution_is_case_insensitive() {
        assert_eq!(leet("A", Level::Basic, true), "4");
        assert_eq!(leet("a", Level::Basic, true), "4");
    }

    #[test]
    fn empty_input_produces_empty_output() {
        assert_eq!(leet("", Level::Extreme, true), "");
        assert_eq!(unleet(""), "");
        assert_eq!(substitution_ratio("", Level::Basic), 0.0);
    }

    #[test]
    fn non_ascii_is_passed_through() {
        assert_eq!(leet("café", Level::Basic, true), "c4fé");
        assert_eq!(leet("ß", Level::Basic, false), "SS");
    }

    #[test]
    fn unleetify_prefers_longer_glyphs() {
        assert_eq!(unleet(r"\/\/"), "w");
        assert_eq!(unleet(r"\/"), "v");
        assert_eq!(unleet(r"/\/\"), "m");
        assert_eq!(unleet("|)"), "d");
        assert_eq!(unleet("|"), "l");
    }

    #[test]
    fn round_trip_recovers_words_without_ambiguous_letters() {
        assert_eq!(unleet(&leet("beast", Level::Advanced, true)), "beast");
    }

    #[test]
    fn round_trip_is_lossy_where_the_mapping_collides() {
        // A digit in the input is indistinguishable from a substitution, so it
        // comes back as the letter that digit stands for.
        assert_eq!(unleet(&leet("a1", Level::Basic, true)), "ai");
        // Case is discarded whenever `preserve_case` is off.
        assert_eq!(unleet(&leet("BeAsT", Level::Advanced, false)), "beast");
    }

    #[test]
    fn ratio_counts_substituted_characters() {
        // "polars": o, a, s substituted at basic level -> 3 of 6.
        assert_eq!(count_substitutions("polars", Level::Basic), 3);
        assert_eq!(substitution_ratio("polars", Level::Basic), 0.5);
    }

    #[test]
    fn level_parsing_rejects_out_of_range() {
        assert!(Level::from_u8(1).is_some());
        assert!(Level::from_u8(3).is_some());
        assert!(Level::from_u8(0).is_none());
        assert!(Level::from_u8(4).is_none());
    }
}

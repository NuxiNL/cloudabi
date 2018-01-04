#[cfg(feature = "bitflags")]
#[macro_use]
extern crate bitflags;

// Minimal implementation of bitflags! in case we can't depend on the bitflags
// crate. Only implements `bits()` and a `from_bits_truncate()` that doesn't
// actually truncate.
#[cfg(not(feature = "bitflags"))]
macro_rules! bitflags {
  (
    $(#[$attr:meta])*
    pub struct $name:ident: $type:ty {
      $($(#[$const_attr:meta])* const $const:ident = $val:expr;)*
    }
  ) => {
    $(#[$attr])*
    #[derive(Copy, Clone, Eq, PartialEq, Hash, Debug)]
    pub struct $name { bits: $type }
    impl $name {
      $($(#[$const_attr])* pub const $const: $name = $name{ bits: $val };)*
      pub fn bits(&self) -> $type { self.bits }
      pub fn from_bits_truncate(bits: $type) -> Self { $name{ bits } }
    }
  }
}

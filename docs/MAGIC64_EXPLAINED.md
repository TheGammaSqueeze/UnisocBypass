# How we shut up a bootloader without having the keys

A story about signatures, stubbornness, and a little bit of shellcode.

This one is for the people who flash their own firmware for fun, know their way
around a `.bat` file, and have at some point stared at a device stuck in
download mode wondering what they did to deserve this. You do not need to be a
developer to follow along. You do need a mild tolerance for the phrase "RSA
signature," which I promise to keep to a minimum.

## The thing that was annoying me

Picture the T820. You unlock the bootloader, everything works, you are happy.
But every single boot it insists on telling you about it:

```
INFO: LOCK FLAG IS : UNLOCK!!!
INFO: Press power button to pause.
WARNNING: LOCK FLAG IS : UNLOCK, SKIP VERIFY!!!
```

(Yes, "WARNNING." Two Ns. Someone at the factory typo'd it years ago and now it
is immortal. I have made my peace with it.)

Then it sits there for a few seconds waiting to see if you want to press power,
which you never do, and finally boots. Three lines of nagging and a pointless
pause, every time. It is the firmware equivalent of a "are you sure?" dialog
that you can never tick "don't ask again" on.

So the goal is simple and petty: make it stop. Remove the text, kill the pause,
boot clean. How hard could it be.

## The obvious plan, and why it failed

The obvious plan is the one you would try first: pull the `uboot` image off the
device, find the bytes that print those lines, poke them out, put it back.

On the older T618 chip this works great. You patch the code, you recalculate a
checksum, you flash it, done. We built a whole toolkit around exactly that.

On the T820 you flash your beautifully edited uboot and the device just... does
not come up. Back to download mode. No explanation, no apology.

Here is why, and it is the whole crux of this article:

**The T820 does not trust anything it did not sign.**

When the chip boots, an early piece of code (the SPL, think of it as the
bouncer at the door) does an RSA signature check on the uboot image before it is
allowed to run. RSA signatures are the kind of math where verifying is easy but
forging is, for practical purposes, impossible without a secret key that lives
inside a factory in a country you do not have a plane ticket to.

So the bouncer looks at your lovingly hand-edited uboot, checks it against the
signature, sees that even one byte changed, and goes "nope." That is not a bug.
That is the entire point of secure boot. It is working exactly as designed, and
the design is specifically to ruin my afternoon.

On the T618 we got away with murder because its bouncer only checked a simple
checksum, which we could just recalculate. The T820's bouncer checks a real
cryptographic signature. We do not have the key. We are never getting the key.

Cue several hours of me trying increasingly stupid things and getting increasing
quantities of "back to download mode" for my trouble.

## The idea that actually works

Here is the trick, and once it clicks it is genuinely delightful.

We are never going to beat the signature check. So we do not try. Instead we
ask a slightly different question:

**What if we do not change the signed image at all, and instead change it
*after* the bouncer has already checked it?**

Think of it like airport security. You cannot bring a bottle of water through
the scanner. Fine. But nobody stops you from buying one at the shop on the other
side. The rule is "no changes before the checkpoint." It says nothing about
after.

So the plan becomes:

1. Keep the original, factory-signed uboot **completely untouched**. Every byte
   identical. The bouncer checks it, the signature matches, everybody is happy.
2. Bolt a tiny extra program onto the end of the file. The signature check does
   not care about this part (more on that in a second).
3. Arrange things so that the moment the signed image is cleared to run, our
   little bolted-on program runs *first*, makes the handful of edits we wanted,
   and *then* hands control to the real uboot.

The edits happen in memory, a fraction of a second after the signature check
passed, on code that is already sitting in RAM cleared for takeoff. The bouncer
already went home. Water for everyone.

This technique is not something we invented, to be clear. It comes from a body
of Unisoc research (the `magic64` method, part of a project called
`unisoc_chipram_signcheck`). We reverse-engineered it, reimplemented it cleanly,
figured out the exact settings for this chip, and confirmed it on real hardware.
But the clever core idea belongs to the people who found it first, and credit
where it is due.

## Okay, but how does it actually run first?

Reasonable question. The signed image has a fixed starting point, the very first
instruction that runs. Normally that instruction is the real uboot's "let's go"
routine.

Our packer does one surgical thing to that starting point: it replaces that
first instruction with a "jump to over there" that points at our bolted-on code.
That is a single instruction. It is technically a change to the image.

"Wait," you say, "you just said we do not change the signed image."

Caught me. Here is the sleight of hand: the signature only covers a specific
region of the file, and we shuffle the layout so that the original payload sits
in the protected region byte-for-byte, while the one instruction we redirect and
all of our new code live in a spot the signature was never calculated over. The
file's own bookkeeping (a little footer that says "the real content is *here*
and it is *this* big") gets nudged to point at the untouched copy. So the
bouncer verifies the pristine original, and the redirect plus our code ride along
in the margins it never looks at.

The end result at boot time:

```
bouncer checks the signed payload  ->  matches, all good
control jumps to OUR code          ->  we copy the payload into place,
                                        apply our edits, flush the caches
our code jumps to the real uboot   ->  uboot runs, none the wiser
```

Our bolted-on program is about a hundred bytes. It is not sophisticated. It
copies the real code into the spot it expects to live in, walks a little list of
"change the value at address X to Y" instructions, tells the processor "hey, the
code changed, re-read it," and jumps to the real entry point. That is the entire
magic trick. The name oversells it.

## The edits themselves

Once we can run code at the right moment, the actual changes are almost boring,
which is exactly how you want your firmware surgery to be. Four tiny edits, each
one a single instruction turned into a "do nothing":

- One kills the `INFO: LOCK FLAG IS : UNLOCK` line and the power-button pause.
- Two kill the `WARNNING: ... SKIP VERIFY` line (it gets printed twice, once to
  the serial console and once to the screen, because of course it does).
- One makes the lock-status check always report "unlocked" without going and
  reading it, just for good measure.

Each of these is a "no operation" instruction, the CPU's version of an awkward
shrug. The code reaches that point, shrugs, moves on, and the annoying thing
never happens.

Finding *which* instructions to shrug out is the part that took real work.
That is a separate rabbit hole involving a disassembler, a lot of coffee, and
matching up cryptic assembly against those exact warning strings. It is
documented in `UMS9620_PORT.md` if you enjoy that sort of pain. For this article
just know: we found them, we wrote down the exact addresses, and the tool checks
that the firmware actually has the instructions we expect at those spots before
it touches anything.

## The part where it bites you (learn from my suffering)

A few things cost me real time. In the spirit of sparing you:

**The image has to be exactly the right size.** The uboot partition is a fixed
size. Our tool adds a bit of stuff, which briefly made the file a hair too big,
and the flashing tool responded with a curt "write flash failed" and zero
further information. Turns out the extra room at the end was all zeroes anyway,
so we just trim it back down to the exact partition size. The tool does this for
you now. It did not do it for me at 2am.

**The load address matters.** Our list of edits says "change the value at
address X." Those addresses depend on where in memory the chip decides to put
uboot. Guess wrong and you are cheerfully overwriting random memory, which goes
about as well as it sounds. We pinned that address down by cross-checking a
bunch of clues in the firmware, and confirmed it on hardware. If you are on the
same device family it just works. If you are on some wildly different build, the
tool will tell you the instructions do not match rather than letting you brick
yourself.

**This does not unlock anything.** Important. This whole technique assumes the
device is *already* unlocked. It removes the nagging and the delay that come
*after* unlocking. It is not a jailbreak, it is not a lock-defeat, it is a mute
button. If your device is locked, this is not the tool for that.

## Why this is the "right" way and not just a hack

The thing I actually like about this approach: it never lies to the security
system. It does not forge a signature. It does not disable the check. It does
not need a leaked key. The chip's secure boot does its job perfectly, verifies a
genuinely-unmodified factory image, and is completely correct to do so. We just
happen to run a hundred bytes of our own code in the half-second afterward.

It is less "picking the lock" and more "noticing the door only locks on the way
in." The lock works. We just walked around it.

Is it fragile? A little. It is tied to a specific chip, a specific load address,
and specific instruction locations. Change the firmware enough and it needs
re-tuning. But for the actual job, which is making a device you own stop yelling
at you every time you turn it on, it is solid, it is repeatable, and it does not
require you to become a cryptographer or steal anything.

Which, honestly, is the most you can ask from an afternoon that started with
three lines of text and one immortal typo.

## Want to just use it?

```bash
python3 tools/patch_uboot_unlock_ums9620.py stock_uboot.img patched_uboot.img
```

That runs all four edits, checks the firmware is what we expect, keeps the
signature valid, sizes it correctly, and hands you an image to flash. If you want
to pick your own edits instead of the preset, `magic_pack_ums9620.py` is the
lower-level tool underneath it.

The gory technical details, exact addresses, and the reverse-engineering notes
live in [`UMS9620_PORT.md`](UMS9620_PORT.md). Go forth and boot quietly.

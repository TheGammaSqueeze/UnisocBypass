# SPL verify call sites (stock UMS512)

Each site matches the pattern: bl verify / cbz w0, ok / mov w0, #5 / bl halt

Code offsets are relative to the start of the code payload (file offset 0x200).

## Site at code offset 0xa3a4 (file offset 0xa5a4)

```
    0xa39c:  2a1303e3
    0xa3a0:  2a1503e4
    0xa3a4:  94000076
    0xa3a8:  34000060
    0xa3ac:  528000a0
    0xa3b0:  97ffff02
```

## Site at code offset 0xa4c0 (file offset 0xa6c0)

```
    0xa4b8:  2a1303e3
    0xa4bc:  52800024
    0xa4c0:  9400002f
    0xa4c4:  34000060
    0xa4c8:  528000a0
    0xa4cc:  97fffebb
```

## Site at code offset 0xa4e8 (file offset 0xa6e8)

```
    0xa4e0:  2a0203e3
    0xa4e4:  52800024
    0xa4e8:  94000025
    0xa4ec:  34000060
    0xa4f0:  528000a0
    0xa4f4:  97fffeb1
```

## Site at code offset 0xa510 (file offset 0xa710)

```
    0xa508:  2a0203e3
    0xa50c:  52800024
    0xa510:  9400001b
    0xa514:  34000060
    0xa518:  528000a0
    0xa51c:  97fffea7
```


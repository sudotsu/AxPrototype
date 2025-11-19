# Courier Handoff Improvements ✅

## Summary

Implemented both suggested improvements to enforce explicit Producer→Courier handoff and prevent Courier from creating undeclared assets.

## Changes Made

### 1. Enhanced Courier Prompt (✅ Implemented)

**Before:**
```python
courier_prompt = (
    f"ObjectiveSpec:\n{objective}\n"
    f"P assets:\n{json.dumps(registry['P'], indent=2)}\n"
    + qa_section_c +
    "Return ONLY a fenced JSON array named C..."
)
```

**After:**
```python
producer_assets = registry["P"]
courier_prompt = (
    f"ObjectiveSpec:\n{objective}\n"
    f"ASSETS TO DEPLOY (DO NOT RECREATE):\n{json.dumps(producer_assets, indent=2)}\n"
    + qa_section_c +
    "Build D1–D7 schedule using ONLY these assets. Return ONLY a fenced JSON array named C..."
)
```

**Benefits:**
- ✅ Explicit constraint: "DO NOT RECREATE" prevents hallucination
- ✅ Clear instruction: "using ONLY these assets"
- ✅ Self-documenting: `producer_assets` variable makes intent clear
- ✅ Reduces LLM confusion about Courier's role boundaries

### 2. Enhanced Validation (✅ Implemented)

**Before:**
```python
def validate_C(items, p_ids: set) -> tuple[bool, str]:
    # Checks p_id in p_ids (implicitly from Producer)
    if it.get("p_id") not in p_ids:
        return False, "C row references unknown P-ID"
```

**After:**
```python
def validate_C(items, p_ids: set, producer_assets: Optional[list] = None) -> tuple[bool, str]:
    # ... existing checks ...

    # Explicit validation: Courier must only use Producer's declared assets
    if producer_assets is not None:
        used_p_ids = {row.get('p_id') for row in items}
        prod_p_ids = {asset.get('p_id') for asset in producer_assets if isinstance(asset, dict)}
        if not used_p_ids.issubset(prod_p_ids):
            missing = used_p_ids - prod_p_ids
            return False, f"Courier used undeclared assets: {missing}"
```

**Benefits:**
- ✅ Explicit validation against Producer's actual assets
- ✅ Better error messages: shows which undeclared assets were used
- ✅ Self-documenting: parameter name makes constraint clear
- ✅ Backward compatible: `producer_assets` is optional

## Why These Changes Matter

### AxProtocol Principle Alignment

1. **Explicit Handoffs (D15-19)**: Producer creates assets → Courier schedules them. No ambiguity.
2. **Role Boundaries**: Courier is banned from creating "api", "ddl", "copy block" (per `role_shapes.json`). These changes enforce this at both prompt and validation levels.
3. **Truth > Obedience**: Clear constraints prevent LLM from "helpfully" creating new assets when it should only schedule existing ones.

### Technical Benefits

1. **Reduced Hallucination**: Explicit "DO NOT RECREATE" reduces chance of Courier inventing assets
2. **Better Debugging**: Error message shows exactly which undeclared P-IDs were used
3. **Maintainability**: `producer_assets` variable makes code self-documenting
4. **Type Safety**: Optional parameter maintains backward compatibility

## Testing

✅ **Import Test**: `from axp.validation import validate_C` ✓
✅ **Linter**: No errors ✓
✅ **Backward Compatibility**: `producer_assets` is optional, existing calls still work ✓

## Files Changed

1. **`axp/orchestration/chain.py`**
   - Extract `producer_assets` explicitly
   - Enhanced Courier prompt with explicit constraints
   - Pass `producer_assets` to `validate_C`

2. **`axp/validation/validators.py`**
   - Added `producer_assets` parameter to `validate_C`
   - Added explicit subset validation
   - Enhanced error messages

## Impact

- **Prompt Level**: LLM receives explicit instruction not to create new assets
- **Validation Level**: System enforces constraint even if LLM tries to bypass
- **Error Messages**: Clear feedback when constraint is violated
- **Code Clarity**: Self-documenting variable names and explicit validation

These changes strengthen the Producer→Courier handoff and prevent role boundary violations.


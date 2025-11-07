# LipKit Development Setup

## Quick Start for Development

### Installation (Development-Friendly)

The `install.sh` script creates a **symlink** to your project folder. This means:

✅ **Auto-detects your Blender version** (4.2, 4.5, etc.)
✅ **Code changes are instant** - no reinstalling!
✅ **Works with multiple Blender versions**

```bash
# Run once
./install.sh

# If you have multiple Blender versions, specify:
./install.sh 4.5
```

### After Installation

1. **Restart Blender** (or start it if not running)
2. **Enable the extension**:
   - Edit → Preferences → Get Extensions
   - Search "LipKit"
   - Toggle enabled
3. **Open the panel**:
   - Press `N` in 3D viewport
   - You should see "LipKit" tab

### Development Workflow

Every time you make code changes:

1. **Edit files** in your IDE (VS Code, PyCharm, etc.)
2. **Reload in Blender**:
   - Press `F3` (or Shift+F9)
   - Type "Reload Scripts"
   - Hit Enter

**That's it!** Changes apply instantly.

### Troubleshooting

#### "Can't find LipKit extension"
- Run `./install.sh` again
- Verify symlink: `ls -la ~/Library/Application\ Support/Blender/4.5/extensions/user_default/lipkit`
- Should show: `lipkit -> /Users/shayanmoradi/Desktop/Work/lipsync-blender`

#### "Reload Scripts doesn't work"
- Try **restarting Blender** completely
- Check **Window → Toggle System Console** for errors

#### "Script errors in console"
- Check the system console for full error traces
- Look for `ModuleNotFoundError` or `SyntaxError`
- Common issues:
  - Circular imports in core modules
  - Missing `register()`/`unregister()` functions
  - Typos in class names

### Project Structure for Development

```
lipsync-blender/          ← You're here
├── install.sh            ← Run this for setup
├── blender_manifest.toml ← Extension metadata
├── lipkit/               ← Main extension folder
│   ├── __init__.py       ← Main registration (start here)
│   ├── operators.py      ← Blender operators
│   ├── ui.py            ← UI panels
│   ├── properties.py     ← Property groups
│   ├── core/            ← Business logic
│   │   ├── __init__.py
│   │   ├── phoneme_engine.py
│   │   ├── controller.py
│   │   ├── mapping.py
│   │   └── animation_engine.py
│   ├── phoneme_providers/
│   ├── visual_systems/
│   └── utils/
└── docs/                ← Documentation
```

### Testing Your Changes

#### Quick Test
```python
# In Blender Python console
import lipkit
print(lipkit.bl_info)

# Or test a specific module
from lipkit.core import LipSyncController
print("✓ Controller module works")
```

#### Test Extension Loads
- Press F3 → "Reload Scripts"
- Check if LipKit panel appears in N-sidebar
- No errors in system console

#### Test a Specific Feature
1. Create test scene with GP object
2. Test operator: `bpy.ops.lipkit.create_controller()`
3. Verify: controller object appears

### Common Development Tasks

#### Add a new operator
1. Add class to `operators.py`
2. Add to `classes` list
3. Reload scripts (F3)

#### Add UI element
1. Edit `ui.py`
2. Add to `draw()` method
3. Reload scripts (F3)

#### Fix a bug in core logic
1. Edit file in `core/`
2. Reload scripts (F3)
3. Test immediately

#### Add a new phoneme provider
1. Create `lipkit/phoneme_providers/my_provider.py`
2. Update `lipkit/phoneme_providers/__init__.py`
3. Reload scripts (F3)

### IDE Setup (Recommended)

#### VS Code
```json
{
  "python.linting.pylintEnabled": true,
  "python.linting.pylintPath": "/Applications/Blender.app/Contents/Resources/4.5/python/bin/python3"
}
```

#### PyCharm
1. Project → Settings → Project Interpreter
2. Add interpreter from: `/Applications/Blender.app/Contents/Resources/4.5/python`

### Git Workflow

The project is git-enabled. Good practices:

```bash
# Make changes
git status

# Commit frequently
git add .
git commit -m "feat: Add new feature"

# Keep README updated
git log --oneline

# Create feature branches
git checkout -b feature/my-feature
```

### Performance Tips

- Reload Scripts doesn't clear `bpy.data` (objects persist)
- If you have stale data, restart Blender
- Use `print()` statements for debugging
- Use system console (Window → Toggle System Console) to see all output

### Debugging

#### Enable Debug Mode
In Blender Preferences → Extensions → LipKit:
- Toggle "Debug Mode"
- Check console for detailed logging

#### Common Errors

**ModuleNotFoundError: No module named 'lipkit.core'**
- Missing `__init__.py` in folder
- Check file path structure

**AttributeError: 'NoneType' object has no attribute...**
- Usually means `bpy.context.scene.lipkit` is None
- Properties not registered yet
- Add `properties.register()` to main `__init__.py`

**No operator registered**
- Check operator `bl_idname` format: `"category.operator_name"`
- Verify it's in `classes` list in operators.py
- Check `register()` function called

### Next Steps

1. **Run install.sh**: `./install.sh`
2. **Restart Blender**
3. **Enable extension** in Preferences
4. **Open N-panel** (Press N)
5. **Start coding!**

Press F3 → "Reload Scripts" to test changes.

---

**Happy developing! 🚀**

# 🎬 LipKit - Quick Reference Card

## For Users: Start Here

| Need | Read | Time |
|------|------|------|
| **What is this?** | README.md | 2 min |
| **How do I install?** | SETUP.md | 10 min |
| **Quick workflow** | docs/QUICKSTART.md | 5 min |
| **Troubleshooting** | README.md + SETUP.md | 5 min |
| **How does it work?** | README.md "How It Works" | 3 min |
| **Deep technical** | docs/ARCHITECTURE.md | 20 min |

## For Developers: Start Here

| Need | Read | Time |
|------|------|------|
| **Project overview** | README.md | 2 min |
| **Code structure** | docs/PROJECT_STRUCTURE.md | 10 min |
| **Architecture** | docs/ARCHITECTURE.md | 20 min |
| **Set up dev env** | docs/DEVELOPMENT.md | 15 min |
| **API reference** | docs/API.md | 30 min |
| **Extend LipKit** | docs/DEVELOPMENT.md "Adding Features" | 20 min |

## Keyboard Shortcuts

In Blender:
- `N` - Open LipKit panel
- `Space` - Play animation
- Middle Mouse - Scrub timeline

## File Locations

- **Main code**: `/lipkit/`
- **Presets**: `/lipkit/presets/` (3 JSON files)
- **Documentation**: `/docs/` (6 markdown files)
- **Config**: Look in Preferences → Extensions → LipKit

## Workflow Steps

1. **Install** → Enable in Preferences
2. **Setup** → Auto-download or select Rhubarb
3. **Prepare** → Create mouth shapes (2D or 3D)
4. **Analyze** → Extract phonemes from audio
5. **Map** → Assign phonemes to shapes
6. **Generate** → Create animation
7. **Play** → Press Space to preview
8. **Adjust** → Move keyframes as needed

## Feature Checklist

✅ Auto-download Rhubarb
✅ Audio format conversion (MP3, M4A, etc.)
✅ Phoneme extraction (real)
✅ Shape keys support
✅ Grease Pencil support
✅ Smooth transitions (easing)
✅ Clean timeline (single controller)
✅ Drivers on shapes
✅ Auto-mapping
✅ Clean All keyframes

## Key Concepts

| Term | Means |
|------|-------|
| **Controller** | Empty object with `phoneme_index` property |
| **Phoneme** | Sound unit (AH, EE, OH, etc.) |
| **Viseme** | Visual mouth shape |
| **Preset** | JSON file mapping phonemes to shapes |
| **Driver** | Expression that links controller to shapes |
| **Easing** | Smooth animation curve between shapes |

## Common Issues

| Problem | Solution |
|---------|----------|
| "Rhubarb not found" | Auto-download, or select Manual mode |
| "Auto-mapped 0 targets" | Name layers/keys X, A, B, C, D, E, F, G, H |
| "No phoneme data" | Click "Analyze Audio" first |
| "Animation doesn't play" | Check controller exists, verify drivers |
| "Layers not switching" | Verify driver expressions in Graph Editor |

## Useful Resources

- 📖 Full docs in `/docs/` folder
- 🔧 GitHub: DanielSWolf/rhubarb-lip-sync (phoneme tool)
- 📺 Blender docs: https://docs.blender.org
- 💬 LipKit discussions: Check repository

## Quick Stats

- **Features**: 15 working + 9 planned
- **Supported Formats**: MP3, WAV, M4A, OGG, FLAC
- **Phonemes**: 9 main shapes (A-H, X) + variants
- **Presets**: 3 included
- **Documentation**: 8 files, 2,282 lines
- **Code**: ~2,300 lines Python

---

**Last Updated**: November 8, 2025
**Version**: Production Ready ✅

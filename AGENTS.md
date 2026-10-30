# Developer Collaboration Workflow

Follow this strict 6-step workflow for all tasks in this repository:

1. **User Request**: The user asks for a feature, change, or bugfix.
2. **Proposal**: Analyze the request and make a concise, concrete proposal/plan.
3. **User Agreement**: Wait for the user's explicit confirmation or feedback.
4. **Autonomous Build (No Mid-Step Inquiries or Redundant Commands)**:
   - Once approved, execute the implementation fully and autonomously.
   - Use direct file tools (`read_file`, `write_file`, `edit_file`) for all inspections and file modifications without running unnecessary shell scripts or one-liners.
   - Do not run unnecessary status checks, intermediate diffs, or scratch execution commands.
   - Compile the project (`cmake --build local-build/cmake --config Release`).
   - Do NOT touch `local-build/OWMB.exe` yet.
   - Do NOT commit or push to git yet.
5. **Ask to Update Local Build**:
   - Inform the user that the build succeeded.
   - Ask via interactive UI prompt (`ask_question`) whether `local-build/OWMB.exe` should be updated with the newly compiled binary.
   - Update only upon explicit user confirmation.
6. **Ask for Git Push**:
   - Ask via interactive UI prompt (`ask_question`) whether the changes should be committed and pushed to git.
   - Commit and push only upon explicit user confirmation.


/**
 * Simple text formatter for robot commands
 * Only styles the text content without changing structure
 */

/**
 * Format robot command text with minimal styling
 * @param commandStr The original robot command string
 * @returns Formatted HTML string with minimal styling
 */
function formatRobotCommandText(commandStr: string): string {
  let formattedText = commandStr;

  // Style section headers with color
  formattedText = formattedText.replace(
    /LOCATE OBJECTS:/g,
    '<span style="color: #3498db; font-weight: bold;">LOCATE OBJECTS:</span>',
  );

  formattedText = formattedText.replace(
    /PLAN ACTIONS:/g,
    '<span style="color: #3498db; font-weight: bold;">PLAN ACTIONS:</span>',
  );

  // Style target headers
  formattedText = formattedText.replace(
    /Target Object:/g,
    '<span style="color: #e74c3c; font-weight: bold;">Target Object:</span>',
  );

  formattedText = formattedText.replace(
    /Target Placement Location:/g,
    '<span style="color: #27ae60; font-weight: bold;">Target Placement Location:</span>',
  );

  // Style colored object tags
  formattedText = colorizeTag(formattedText, "red", "#e74c3c");
  formattedText = colorizeTag(formattedText, "green", "#27ae60");
  formattedText = colorizeTag(formattedText, "blue", "#3498db");
  formattedText = colorizeTag(formattedText, "yellow", "#f1c40f");
  formattedText = colorizeTag(formattedText, "cube", "#9b59b6");

  // Style coordinate tags
  formattedText = formattedText.replace(
    /<\|(\d+-\d+)\|>/g,
    '<span style="color: #34495e;">&lt;|$1|&gt;</span>',
  );

  formattedText = formattedText.replace(
    /<\|(local-\d+-\d+)\|>/g,
    '<span style="color: #7f8c8d;">&lt;|$1|&gt;</span>',
  );

  // Style step numbers
  formattedText = formattedText.replace(
    /Step \d+:/g,
    (match) =>
      `<span style="color: #2c3e50; font-weight: bold;">${match}</span>`,
  );

  // Style numerical values
  formattedText = formattedText.replace(
    /\b(\d+)\b/g,
    '<span style="color: #e67e22;">$1</span>',
  );

  // Style array brackets and quotes
  formattedText = formattedText.replace(
    /\[|\]/g,
    (match) =>
      `<span style="color: #3498db; font-weight: bold;">${match}</span>`,
  );

  formattedText = formattedText.replace(
    /","/g,
    '<span style="color: #7f8c8d;">","</span>',
  );

  return formattedText;
}

/**
 * Helper function to colorize specific tags
 * @param text Input text
 * @param keyword Keyword to colorize
 * @param color Color to use
 * @returns Text with colorized tags
 */
function colorizeTag(text: string, keyword: string, color: string): string {
  const tagRegex = new RegExp(`<\\|${keyword}\\|>`, "g");
  return text.replace(
    tagRegex,
    `<span style="color: ${color};">&lt;|${keyword}|&gt;</span>`,
  );
}

export { formatRobotCommandText };

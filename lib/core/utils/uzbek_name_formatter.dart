// Simple utility to format Uzbek names consistently
class UzbekNameFormatter {
  static String format(String name) {
    if (name.isEmpty) return "";
    
    // Split by space
    final parts = name.trim().split(RegExp(r'\s+'));
    return parts.map((part) {
      if (part.isEmpty) return "";
      
      // Basic Title Case
      // This handles `Navro'Z` -> `Navro'z` because substring(1).toLowerCase() 
      // will lowercase the 'Z' properly.
      String formatted = part[0].toUpperCase() + part.substring(1).toLowerCase();
      
      // Specifically target known problem patterns like 'O‘G‘Li' -> 'O‘g‘li' if needed
      // But standard TitleCase handles this for the ASCII range and common unicode.
      
      return formatted;
    }).join(' ');
  }
}

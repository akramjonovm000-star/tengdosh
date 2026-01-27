import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'dart:convert';

class LocalDatabaseService {
  static Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('talabahamkor.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future _createDB(Database db, int version) async {
    const textType = 'TEXT NOT NULL';
    const idType = 'INTEGER PRIMARY KEY AUTOINCREMENT';
    const intType = 'INTEGER NOT NULL';

    // 1. Dashboard Cache
    await db.execute('''
      CREATE TABLE dashboard (
        id $idType,
        student_id $intType,
        semester_code $textType,
        data $textType,
        updated_at $textType
      )
    ''');

    // 2. Attendance Cache
    await db.execute('''
      CREATE TABLE attendance (
        id $idType,
        student_id $intType,
        semester_code $textType,
        data $textType,
        updated_at $textType
      )
    ''');

    // 3. Subjects Cache
    await db.execute('''
      CREATE TABLE subjects (
        id $idType,
        student_id $intType,
        semester_code $textType,
        data $textType,
        updated_at $textType
      )
    ''');
    
    // 4. Schedule Cache
    await db.execute('''
      CREATE TABLE schedule (
        id $idType,
        student_id $intType,
        semester_code $textType,
        data $textType,
        updated_at $textType
      )
    ''');
    
    // Create indices
    await db.execute('CREATE INDEX idx_dashboard_student ON dashboard (student_id)');
    await db.execute('CREATE INDEX idx_attendance_student ON attendance (student_id, semester_code)');
    await db.execute('CREATE INDEX idx_subjects_student ON subjects (student_id, semester_code)');
    await db.execute('CREATE INDEX idx_schedule_student ON schedule (student_id, semester_code)');
  }

  // --- Helper Methods ---

  Future<void> saveCache(String table, int studentId, Map<String, dynamic> data, {String? semesterCode}) async {
    try {
      final db = await database;
      final jsonStr = jsonEncode(data);
      final now = DateTime.now().toIso8601String();

      await db.insert(
        table,
        {
          'student_id': studentId,
          'semester_code': semesterCode ?? 'all',
          'data': jsonStr,
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    } catch (e) {
      print("Local DB Save Cache Error ($table): $e");
      // If schema mismatch, wipe and let next call succeed (self-healing)
      if (e.toString().contains("no such column") || e.toString().contains("has no column")) {
        await _clearAndRecreateTable(table);
      }
    }
  }

  Future<Map<String, dynamic>?> getCache(String table, int studentId, {String? semesterCode}) async {
    try {
      final db = await database;
      final maps = await db.query(
        table,
        where: 'student_id = ? AND semester_code = ?',
        whereArgs: [studentId, semesterCode ?? 'all'],
        limit: 1,
      );

      if (maps.isNotEmpty) {
        return jsonDecode(maps.first['data'] as String) as Map<String, dynamic>;
      }
    } catch (e) {
      print("Local DB Get Cache Error ($table): $e");
      if (e.toString().contains("no such column")) {
        await _clearAndRecreateTable(table);
      }
    }
    return null;
  }

  Future<void> _clearAndRecreateTable(String table) async {
     try {
       final db = await database;
       await db.execute("DROP TABLE IF EXISTS $table");
       // Re-run the specific creation part
       if (table == 'dashboard') {
         await db.execute('''
          CREATE TABLE dashboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester_code TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL
          )
         ''');
         await db.execute('CREATE INDEX idx_dashboard_student ON dashboard (student_id)');
       } else if (table == 'attendance') {
         await db.execute('''
          CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester_code TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL
          )
         ''');
         await db.execute('CREATE INDEX idx_attendance_student ON attendance (student_id, semester_code)');
       }
       // Add other tables if needed
     } catch (e) {
       print("Failed to self-heal table $table: $e");
     }
  }
  
  Future<void> clearCache() async {
    final db = await database;
    await db.delete('dashboard');
    await db.delete('attendance');
    await db.delete('subjects');
    await db.delete('schedule');
  }

  Future close() async {
    final db = await database;
    db.close();
  }
}

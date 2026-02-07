class University {
  final String name;
  final String code;
  final String apiBaseUrl;

  const University({
    required this.name,
    required this.code,
    required this.apiBaseUrl,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is University &&
          runtimeType == other.runtimeType &&
          code == other.code;

  @override
  int get hashCode => code.hashCode;
}

const List<University> supportedUniversities = [
  // --- Priority (User Requested) ---
  University(name: "O'zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti", code: "uzjoku", apiBaseUrl: "https://student.uzjoku.uz/rest/v1"),
  University(name: "Jizzax davlat pedagogika universiteti", code: "jdpu", apiBaseUrl: "https://student.jdpu.uz/rest/v1"),
  University(name: "Toshkent davlat iqtisodiyot universiteti (TDIU)", code: "tsue", apiBaseUrl: "https://talaba.tsue.uz/rest/v1"),

  // --- All Others ---
  // A
  University(name: "Andijon davlat universiteti", code: "adu", apiBaseUrl: "https://student.adu.uz/rest/v1"),
  University(name: "Andijon mashinasozlik instituti", code: "andmiedu", apiBaseUrl: "https://student.andmiedu.uz/rest/v1"),
  University(name: "Andijon davlat tibbiyot instituti", code: "adti", apiBaseUrl: "https://student.adti.uz/rest/v1"),
  University(name: "Andijon qishloq xo'jaligi va agrotexnologiyalar instituti", code: "aqxai", apiBaseUrl: "https://student.aqxai.uz/rest/v1"),
  University(name: "Andijon davlat chet tillari instituti", code: "adchti", apiBaseUrl: "https://student.adchti.uz/rest/v1"),
  University(name: "Andijon iqtisodiyot va qurilish instituti", code: "aiqi", apiBaseUrl: "https://student.aiqi.uz/rest/v1"),

  // B
  University(name: "Buxoro davlat universiteti", code: "buxdu", apiBaseUrl: "https://student.buxdu.uz/rest/v1"),
  University(name: "Buxoro muhandislik-texnologiya instituti", code: "bmti", apiBaseUrl: "https://student.bmti.uz/rest/v1"),
  University(name: "Buxoro davlat tibbiyot instituti", code: "bsmi", apiBaseUrl: "https://student.bsmi.uz/rest/v1"),
  University(name: "Buxoro davlat pedagogika instituti", code: "buxdpi", apiBaseUrl: "https://student.buxdpi.uz/rest/v1"),
  University(name: "Buxoro tabiiy resurslarni boshqarish instituti", code: "tiiamebb", apiBaseUrl: "https://student.tiiamebb.uz/rest/v1"),

  // F
  University(name: "Farg'ona davlat universiteti", code: "fdu", apiBaseUrl: "https://student.fdu.uz/rest/v1"),
  University(name: "Farg'ona politexnika instituti", code: "ferpi", apiBaseUrl: "https://student.ferpi.uz/rest/v1"),
  University(name: "Farg'ona jamoat salomatligi tibbiyot instituti", code: "fjsti", apiBaseUrl: "https://student.fjsti.uz/rest/v1"),

  // G
  University(name: "Guliston davlat universiteti", code: "guldu", apiBaseUrl: "https://student.guldu.uz/rest/v1"),
  University(name: "Guliston davlat pedagogika instituti", code: "gspi", apiBaseUrl: "https://student.gspi.uz/rest/v1"),

  // J
  University(name: "Jizzax politexnika instituti", code: "jizpi", apiBaseUrl: "https://student.jizpi.uz/rest/v1"),
  University(name: "Jahon iqtisodiyoti va diplomatiya universiteti", code: "uwed", apiBaseUrl: "https://student.uwed.uz/rest/v1"),

  // N
  University(name: "Navoiy davlat pedagogika instituti", code: "nspi", apiBaseUrl: "https://student.nspi.uz/rest/v1"),
  University(name: "Navoiy davlat konchilik va texnologiyalar universiteti", code: "nDKTU", apiBaseUrl: "https://student.nDKTU.uz/rest/v1"),
  University(name: "Namangan davlat universiteti", code: "namdu", apiBaseUrl: "https://student.namdu.uz/rest/v1"),
  University(name: "Namangan muhandislik-qurilish instituti", code: "nammqi", apiBaseUrl: "https://student.nammqi.uz/rest/v1"),
  University(name: "Namangan muhandislik-texnologiya instituti", code: "nammti", apiBaseUrl: "https://student.nammti.uz/rest/v1"),
  University(name: "Namangan to'qimachilik sanoati instituti", code: "ntsi", apiBaseUrl: "https://student.ntsi.uz/rest/v1"),
  University(name: "Nukus davlat pedagogika instituti", code: "ndpi", apiBaseUrl: "https://student.ndpi.uz/rest/v1"),
  University(name: "Nukus konchilik instituti", code: "ndki", apiBaseUrl: "https://student.ndki.uz/rest/v1"),

  // O
  University(name: "O'zbekiston Milliy universiteti", code: "nuu", apiBaseUrl: "https://student.nuu.uz/rest/v1"),
  University(name: "O'zbekiston davlat jahon tillari universiteti", code: "uzswlu", apiBaseUrl: "https://student.uzswlu.uz/rest/v1"),
  University(name: "O'zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti", code: "uzjoku", apiBaseUrl: "https://student.uzjoku.uz/rest/v1"),
  University(name: "O'zbekiston davlat san'at va madaniyat instituti", code: "dsmi", apiBaseUrl: "https://student.dsmi.uz/rest/v1"),
  University(name: "O'zbekiston davlat konservatoriyasi", code: "konservatoriya", apiBaseUrl: "https://student.konservatoriya.uz/rest/v1"),
  University(name: "O'zbekiston davlat jismoniy tarbiya va sport universiteti", code: "jtsu", apiBaseUrl: "https://student.jtsu.uz/rest/v1"),
  University(name: "O'zbekiston xalqaro islom akademiyasi", code: "iiau", apiBaseUrl: "https://student.iiau.uz/rest/v1"),

  // Q
  University(name: "Qarshi davlat universiteti", code: "qarshidu", apiBaseUrl: "https://student.qarshidu.uz/rest/v1"),
  University(name: "Qarshi muhandislik-iqtisodiyot instituti", code: "qmii", apiBaseUrl: "https://student.qmii.uz/rest/v1"),
  University(name: "Qoraqalpoq davlat universiteti", code: "karsu", apiBaseUrl: "https://student.karsu.uz/rest/v1"),
  University(name: "Qo'qon davlat pedagogika instituti", code: "kspi", apiBaseUrl: "https://student.kspi.uz/rest/v1"),

  // S
  University(name: "Samarqand davlat universiteti", code: "samdu", apiBaseUrl: "https://student.samdu.uz/rest/v1"),
  University(name: "Samarqand davlat tibbiyot universiteti", code: "sammu", apiBaseUrl: "https://student.sammu.uz/rest/v1"),
  University(name: "Samarqand davlat chet tillari instituti", code: "samdchti", apiBaseUrl: "https://student.samdchti.uz/rest/v1"),
  University(name: "Samarqand davlat arxitektura-qurilish universiteti", code: "samdaqu", apiBaseUrl: "https://student.samdaqu.edu.uz/rest/v1"),
  University(name: "Samarqand iqtisodiyot va servis instituti", code: "sies", apiBaseUrl: "https://student.sies.uz/rest/v1"),
  University(name: "Samarqand veterinariya meditsinasi instituti", code: "ssuv", apiBaseUrl: "https://student.ssuv.uz/rest/v1"),

  // T
  University(name: "Toshkent davlat texnika universiteti", code: "tdtu", apiBaseUrl: "https://student.tdtu.uz/rest/v1"),
  University(name: "Toshkent axborot texnologiyalari universiteti (TATU)", code: "tuit", apiBaseUrl: "https://student.tuit.uz/rest/v1"),
  // TSUE moved to top
  University(name: "Toshkent davlat pedagogika universiteti", code: "tdpu", apiBaseUrl: "https://student.tdpu.uz/rest/v1"),
  University(name: "Toshkent davlat yuridik universiteti", code: "tsul", apiBaseUrl: "https://student.tsul.uz/rest/v1"),
  University(name: "Toshkent moliya instituti", code: "tfi", apiBaseUrl: "https://student.tfi.uz/rest/v1"),
  University(name: "Toshkent to'qimachilik va yengil sanoat instituti", code: "ttyesi", apiBaseUrl: "https://student.ttyesi.uz/rest/v1"),
  University(name: "Toshkent kimyo-texnologiya instituti", code: "tcti", apiBaseUrl: "https://student.tcti.uz/rest/v1"),
  University(name: "Toshkent davlat transport universiteti", code: "tstu", apiBaseUrl: "https://student.tstu.uz/rest/v1"),
  University(name: "Toshkent davlat sharqshunoslik universiteti", code: "tsuos", apiBaseUrl: "https://student.tsuos.uz/rest/v1"),
  University(name: "Toshkent tibbiyot akademiyasi", code: "tma", apiBaseUrl: "https://student.tma.uz/rest/v1"),
  University(name: "Toshkent farmatsevtika instituti", code: "pharmi", apiBaseUrl: "https://student.pharmi.uz/rest/v1"),
  University(name: "Termiz davlat universiteti", code: "terdu", apiBaseUrl: "https://student.terdu.uz/rest/v1"),
  University(name: "Termiz muhandislik-texnologiya instituti", code: "tmti", apiBaseUrl: "https://student.tmti.uz/rest/v1"),
  University(name: "Termiz davlat pedagogika instituti", code: "termizdpi", apiBaseUrl: "https://student.termizdpi.uz/rest/v1"),

  // U
  University(name: "Urganch davlat universiteti", code: "urdu", apiBaseUrl: "https://student.urdu.uz/rest/v1"),
  University(name: "Urganch davlat pedagogika instituti", code: "urspi", apiBaseUrl: "https://student.urspi.uz/rest/v1"),
  
  // Others
  University(name: "Chirchiq davlat pedagogika universiteti", code: "cspi", apiBaseUrl: "https://student.cspi.uz/rest/v1"),
];

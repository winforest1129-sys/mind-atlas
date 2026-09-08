# -*- coding: utf-8 -*-
"""⭐引用元の振り分けの、⚠**手で決めたぶん**（2026-09-09）。

⭐物差しと理由は `_papers/判定メモ.md` に書いた。⭐ここは url をキーにした表だけ。
⚠**url が変わったら当たらなくなる**ので、直すときは両方見ること。
"""
# ⭐`要確認` のうち、**論文として採る**もの
TAKE = {
 'http://www.columbia.edu/~nb2229/docs/zaki-bolger-ochsner-emot-2009.pdf',
 'https://karger.com/hde/article-abstract/23/6/400/156432/Dialectical-SchemataA-Framework-for-the-Empirical',
 'https://econtent.hogrefe.com/doi/10.1027/1864-9335/a000186',
 'https://elainehatfield.com/ch87.pdf',
 'https://gershmanlab.com/pubs/PatzeltHartleyGershman18.pdf',
 'https://scan.psych.columbia.edu/papers/Olsson_et_al_2016.pdf',
 'https://www.annualreviews.org/doi/10.1146/annurev-cellbio-100814-125308',
 'https://bmcgenomics.biomedcentral.com/articles/10.1186/s12864-020-6583-3',
 'https://www.psychiatryonline.org/doi/10.1176/appi.focus.11.2.189',
 'https://philarchive.org/archive/REIATI',
 'https://www.cultivatingleadership.com/site/uploads/Berger-Chapter-14-Prepublication-Draft-1.pdf',
 'https://www.apa.org/pubs/books/The-Dark-Side-of-Personality-Intro-Sample.pdf',
 'https://www.thetedkarchive.com/library/alan-barnard-the-kalahari-debate-a-bibliographical-essay',
 'https://www.jacc.org/doi/10.1016/j.jacc.2011.06.018',
}
# ⭐url の頭が合えば採る（同じ論文に長い url が2通りあるもの）
TAKE_PREFIX = (
 'https://integral-review.org/issues/vol_11_no_3_laske',
 'https://ora.ox.ac.uk/objects/uuid:a9374625',
 'https://web.sas.upenn.edu/ggoodwin/files/2016/08/Landy-Goodwin-2015',
 'https://researchportal.coachingfederation.org/Document/Pdf/2030.pdf',
)
# ⚠`論文` に振り分けられたが、**論文ではない**もの（宿主で拾いすぎたぶん）
DROP = {
 'https://www.researchgate.net/publication/12655757_Emotion_regulation_in_the_workplace_A_new_way_to_conceptualize_emotional_labor',
}
DROP_PREFIX = (
 'https://archive.org/details/mit_press_book_',      # ⭐『能動的推論』の本まるごと
 'https://archive.org/details/dialecticalthink',     # ⭐Basseches 1984 の本まるごと
 'https://www.hup.harvard.edu/',                     # 版元
 'https://www.apa.org/pubs/books/4318141',           # 書籍そのもの
 'https://talyarkoni.org/blog/',                     # ⚠ブログ
 'https://www.kcl.ac.uk/news/',                      # 大学の声明
 'https://bpspsychub.onlinelibrary.wiley.com/doi/full/10.1111/papt.12508',  # 著者不明の告示
 'https://scholar.harvard.edu/',                     # 著者の出版一覧
 'https://davidakenny.net/',                         # 解説ページ
 'http://www.smellosophy.com/',                      # CV
 'https://www.discovermagazine.com/',                # 報道
 'https://www.thebookseller.com/',                   # 報道
 'https://www.polytec.com/',                         # プレス
 'http://www.authentic-a.com/',                      # 会社
 'https://primate-society.com/',                     # 学会の新刊紹介
 'https://www.harashobo.co.jp/', 'https://www.kyoto-up.or.jp/',
 'https://www.kinokuniya.co.jp/',
)


def decide(kind, url):
    """⭐自動の振り分け `kind` に、手で決めたぶんをかぶせる。"""
    u = url or ''
    if u in DROP or any(u.startswith(p) for p in DROP_PREFIX):
        return 'ちがう'
    if u in TAKE or any(u.startswith(p) for p in TAKE_PREFIX):
        return '論文'
    return kind


# ============================================================================
# ⭐手当ての表（2026-09-09）── ⚠**外部と食い違ったものを、1件ずつ目で見て決めた。**
#   ⭐理由を必ず書く。⚠理由の書けないものは直さない（推測で埋めない）。
# ============================================================================
FIX = {
 # ⭐DOI が url に無くて取れなかったもの（題で探して目で確かめた）
 'https://www.semanticscholar.org/paper/7842d6edf33f2c652d5c70613b12f56f176bf7d8': {
   'doi': '10.1159/000286529', 'year': 1973,
   'why': '⚠Crossref は 2010 と返すが、これは Karger の電子化年。原典は 1973 年'},
 'https://karger.com/hde/article-abstract/23/6/400/156432/Dialectical-SchemataA-Framework-for-the-Empirical': {
   'doi': '10.1159/000272600', 'year': 1980,
   'why': '⚠同じく Karger の電子化年（2009）に引きずられる。原典は 1980 年'},
 'https://www.sciencedirect.com/science/article/abs/pii/S2352154617301249': {
   'doi': '10.1016/j.cobeha.2018.05.006',
   'why': '題で探して確かめた（Evrard 2018, Current Opinion in Behavioral Sciences）'},
 'https://www.sciencedirect.com/science/article/pii/S1359178923000952': {
   'doi': '10.1016/j.avb.2023.101908',
   'why': '題で探して確かめた（Nielsen ら, Aggression and Violent Behavior）'},
 'https://researchportal.coachingfederation.org/Document/Pdf/2030.pdf': {
   'doi': '10.1177/174183051401208s03',
   'why': '題で探して確かめた（Van Thor 2014）'},
 'https://philarchive.org/archive/REIATI': {
   'doi': '10.1007/978-3-030-67220-1_9',
   'why': '⚠⚠**引用元の著者名「Reinbold C」は誤りだった。正しくは Robert Reimer**'
          '（Springer の章・2021）。⭐2026-09-09 に `見かけの因果関係` の refs を直した'},
 # ⭐年だけ、外部より引用元のほうが正しいもの
 'https://onlinelibrary.wiley.com/doi/10.1111/j.1469-8676.1992.tb00240.x': {
   'year': 1992,
   'why': '⚠Crossref は 2007 と返すが、これは Wiley のバックファイル収録年。原典は 1992 年'},
 # ⚠引用元のほうが誤っていたもの
 'https://onlinelibrary.wiley.com/doi/10.1111/tops.12689': {
   'year': 2023,
   'why': '⚠⚠**引用元の「2026年」は誤り。**Topics in Cognitive Science 2023。'
          'ノード `表象ドリフト` の記述を直すこと'},
 'https://pubmed.ncbi.nlm.nih.gov/11119782/': {
   'year': 2000,
   'why': '⚠引用元の「Denollet 1995ほか」は不正確。この論文は 2000 年'},
}

# ⚠⚠**引用元の題と url が、別の論文を指しているもの。**
#   ⭐ノードを直すまで、論文ノードは作らない（作ると地図に嘘が入る）。
# ⭐2026-09-09：どちらも**その日のうちに直した**ので、いまは空。
#   ⚠**見つかった経緯は残しておく**（同じ形の事故は、またありうる）:
#   ① `アイオワ・ギャンブリング課題`＝題は「Bechara ら 1994」なのに、
#      url は Aram ら2019 の総説だった → ⭐原典の DOI に差し替えた
#   ② `グッドハートの法則`＝題は「Strathern 1997」なのに、
#      url は Mattson ら2021 の別論文だった → ⭐European Review の原典に差し替えた
#   ⭐**どちらも、書誌の照合（年が合うか）が掘り当てた。**
MISMATCH = {}

# ⭐外部（Crossref／PubMed）に載っていないが、引用元の記述がはっきりしているもの。
#   ⚠**「外部で確定できなかった」と必ず明示する。**
HAND = {
 'https://www.semanticscholar.org/paper/Paradigm-shift-to-the-integrative-Big-Five-trait-John-Naumann/': {
   'year': 2008, 'authors': ['John', 'Naumann', 'Soto'],
   'title': 'Paradigm Shift to the Integrative Big Five Trait Taxonomy',
   'journal': 'Handbook of Personality: Theory and Research (3rd ed.)',
   'how': '⚠外部で確定できず（書籍の章で DOI が無い）。引用元の記述による'},
 "https://integral-review.org/issues/vol_11_no_3_laske_laske's_dialectical_thought_form_framework.pdf": {
   'year': 2015, 'authors': ['Laske'],
   'title': "Laske's Dialectical Thought Form Framework (DTF)",
   'journal': 'Integral Review 11(3)',
   'how': '⚠外部で確定できず（Crossref に載っていない公開誌）。引用元の記述による'},
}

# ⚠論文ではないと決め直したもの（振り分けのあとで分かったぶん）
LATE_DROP = {
 'https://www.ncbi.nlm.nih.gov/books/NBK551567/',        # StatPearls＝教科書の項目
 'https://www.cell.com/trends/cognitive-sciences/comments/S1364-6613(05)00033-1',  # 往復書簡
}


# ⭐2026-09-09・全件を洗い直して見つけたぶん（照合を締め直したあと）
HAND.update({
 'https://www.semanticscholar.org/paper/The-Case-Against-Type-Dynamics-Reynierse/': {
   'year': 2009, 'authors': ['Reynierse'],
   'title': 'The Case Against Type Dynamics',
   'journal': 'Journal of Psychological Type 69(1)',
   'how': '⚠外部で確定できず（Crossref に無い専門誌）。引用元の記述による。'
          '⚠⚠題で探すと「Type Theory Revisited」という別の章に化けたので、手で入れた'},
})
LATE_DROP.update({
 # ⚠外部で確定できない（Crossref は Barnard の別論文を返す）。refs には残す
 'https://www.thetedkarchive.com/library/alan-barnard-the-kalahari-debate-a-bibliographical-essay',
 # ⚠筆頭著者が特定できない（学会名義）。物差しどおり論文としない
 'https://www.psychiatryonline.org/doi/10.1176/appi.focus.11.2.189',
})


# ⭐2026-09-09・題での照合を締めたあとに落ちたが、⭐中身は合っていたもの。
#   ⚠引用元に年が書かれていないので機械では通せない。⭐目で確かめて手で入れる。
HAND.update({
 'https://elainehatfield.com/ch87.pdf': {
   'year': 2009, 'authors': ['Hatfield', 'Rapson', 'Le'],
   'title': 'Emotional Contagion and Empathy',
   'journal': 'The Social Neuroscience of Empathy (MIT Press)',
   'how': '⭐題で探して目で確かめた（Crossref）。⚠引用元に年が無いので機械では通せなかった'},
 'https://www.cultivatingleadership.com/site/uploads/Berger-Chapter-14-Prepublication-Draft-1.pdf': {
   'year': 2023, 'authors': ['Berger'],
   'title': 'Using the Subject-Object Interview to Promote and Assess Self-Development',
   'journal': 'The Cambridge Handbook of Personal Development',
   'how': '⭐題で探して目で確かめた（Crossref）。'
          '⚠引用元は刊行前の草稿PDFで、これは刊行版。年は刊行版のもの'},
 # ⭐Landy & Goodwin 2015 は、同じ論文が SAGE の url でも引かれていて、そちらは通っている。
 #   ⚠こちらは「同メタ分析の全文PDF」という題で年が無く、⭐**中国語の別論文に化けた**。
 #   ⭐DOI を直に当てて、同じ論文として畳む。
 'https://web.sas.upenn.edu/ggoodwin/files/2016/08/Landy-Goodwin-2015-Disgust-meta-analysis-PERSPECTIVES-18zcxr2.pdf': {
   'year': 2015, 'authors': ['Landy', 'Goodwin'],
   'title': 'Does Incidental Disgust Amplify Moral Judgment? A Meta-Analytic Review of Experimental Evidence',
   'journal': 'Perspectives on Psychological Science',
   'doi': '10.1177/1745691615583128',
   'how': '⭐同じ論文が SAGE の url でも引かれている。DOI を直に当てた'},
})

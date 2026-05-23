"""
Intent Classifier module for RIADAH ERP chatbot.
Uses TF-IDF vectorization with scikit-learn to classify user messages into intents.
"""

import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    TF-IDF based intent classifier for Arabic chat messages.

    Supported intents:
        - greeting: مرحباً، أهلاً، السلام عليكم، صباح الخير، ...
        - farewell: مع السلامة، وداعاً، إلى اللقاء، ...
        - sales_query: كم المبيعات، تقرير المبيعات، فواتير البيع، ...
        - hr_query: الموظفين، الإجازات، الرواتب، الحضور، ...
        - financial_query: الأرباح، الخسائر، الميزانية، المصروفات، ...
        - purchases_query: المشتريات، الموردين، أوامر الشراء، ...
        - crm_query: العملاء، الفرص، التذاكر، التنبؤ، ...
        - projects_query: المشاريع، المهام، المخاطر، ...
        - pos_query: نقاط البيع، الكاشير، فاتورة مبيعات، ...
        - payroll_query: الرواتب، كشف الراتب، البدلات، ...
        - general_question: كيف، ما هو، لماذا، هل، ...
    """

    INTENT_LABELS = [
        'greeting',
        'farewell',
        'sales_query',
        'hr_query',
        'financial_query',
        'purchases_query',
        'crm_query',
        'projects_query',
        'pos_query',
        'payroll_query',
        'general_question',
    ]

    # Arabic training phrases for each intent
    TRAINING_DATA = {
        'greeting': [
            'مرحباً',
            'مرحبا',
            'أهلاً',
            'أهلا',
            'السلام عليكم',
            'سلام عليكم',
            'صباح الخير',
            'مساء الخير',
            'هلا',
            'هاي',
            'أهلاً وسهلاً',
            'يا هلا',
            'كيف حالك',
            'كيفك',
            'شخبارك',
            'أشكرك',
            'شكراً لك',
            'شكرا',
            'شكرا جزيلا',
            'مشكور',
            'السلام عليكم ورحمة الله',
            'سلام',
            'حياك الله',
            'أهلاً بك',
            'مرحبا بك',
        ],
        'farewell': [
            'مع السلامة',
            'وداعاً',
            'وداعا',
            'إلى اللقاء',
            'الى اللقاء',
            'باي',
            'مع السلامه',
            'في أمان الله',
            'يوم سعيد',
            'تصبح على خير',
            'مساء النور',
            'الله يسعدك',
            'الله يحفظك',
            'أراك لاحقاً',
            'خلاص',
            'تمام شكراً',
        ],
        'sales_query': [
            'كم المبيعات',
            'تقرير المبيعات',
            'فواتير البيع',
            'إجمالي المبيعات',
            'مبيعات اليوم',
            'مبيعات الشهر',
            'أكثر المنتجات مبيعاً',
            'أفضل مبيعات',
            'أرقام المبيعات',
            'إحصائيات المبيعات',
            'كم بعنا اليوم',
            'كم الايرادات من المبيعات',
            'الفواتير المباعة',
            'كم عدد الفواتير',
            'عملاء جدد',
            'كم عميل لدينا',
            'تقرير العملاء',
            'طلبات البيع',
            'عروض الأسعار',
            'كم قيمة المبيعات',
            'مبيعات هذا الأسبوع',
            'أداء فريق المبيعات',
            'ترتيب مندوبي المبيعات',
            'أفضل مندوب مبيعات',
            'مبيعات الفرع',
            'العملاء المتأخرين في الدفع',
        ],
        'hr_query': [
            'كم عدد الموظفين',
            'قائمة الموظفين',
            'الإجازات',
            'مواعيد الحضور',
            'سجل الحضور',
            'الغيابات',
            'التأخير',
            'رواتب الموظفين',
            'كشف الرواتب',
            'تقييم الأداء',
            'القسم الوظيفي',
            'الأقسام',
            'التوظيف',
            'موظفين جدد',
            'إنهاء خدمات',
            'طلبات إجازة',
            'ساعات العمل',
            'البدلات',
            'الخصومات',
            'إجمالي الرواتب',
            'كم نسبة الحضور',
            'تقرير الموارد البشرية',
            'بيانات الموظف',
            'الهيكل التنظيمي',
            'التدريب',
            'التوظيف والتعيين',
            'من حاضر اليوم',
            'كم متغيب',
        ],
        'financial_query': [
            'كم الأرباح',
            'ما الخسائر',
            'الميزانية',
            'المصروفات',
            'الإيرادات',
            'الميزانية العمومية',
            'قائمة الدخل',
            'التدفق النقدي',
            'كم المال المتوفر',
            'المصروفات الشهرية',
            'إجمالي الإيرادات',
            'الربح الصافي',
            'الربح الإجمالي',
            'تكاليف التشغيل',
            'الذمم المدينة',
            'الذمم الدائنة',
            'الفواتير غير المدفوعة',
            'المصروفات المعلقة',
            'تقرير مالي',
            'الإحصائيات المالية',
            'قيمة الفواتير المستحقة',
            'المبالغ المحصلة',
            'ضريبة',
            'الضرائب',
            'القيد المحاسبي',
            'الأرصدة',
            'مركز مالي',
            'الدفعات المستلمة',
        ],
        'purchases_query': [
            'كم المشتريات',
            'تقرير المشتريات',
            'الموردين',
            'أوامر الشراء',
            'طلبات الشراء',
            'الموردين النشطين',
            'أفضل الموردين',
            'تقييم الموردين',
            'مشتريات الشهر',
            'إجمالي المشتريات',
            'كم طلب شراء',
            'الموردين المتأخرين',
            'حالة طلبات الشراء',
            'مقارنة أسعار الموردين',
            'قيمة البضاعة المشتراة',
            'تقرير الموردين',
            'أوامر الشراء المعلقة',
            'المشتريات المستلمة',
            'كم مبلغ المشتريات',
            'المورد',
            'استيراد بضائع',
            'تصدير بضائع',
        ],
        'crm_query': [
            'إدارة العملاء',
            'العملاء المحتملين',
            'الفرص',
            'خط أنبوب المبيعات',
            'التذاكر',
            'شكاوى العملاء',
            'عملاء VIP',
            'تقسيم العملاء',
            'تحليل العملاء',
            'كم عميل محتمل',
            'فرصة بيع جديدة',
            'مراحل البيع',
            'عروض أسعار للعملاء',
            'رحلة العميل',
            'رضا العملاء',
            'العملاء المفقودين',
            'نظام CRM',
            'تذاكر الدعم',
            'طلب دعم فني',
            'مشكلة عميل',
            'متابعة العملاء',
            'أفضل العملاء',
            'عملاء على وشك الفقدان',
        ],
        'projects_query': [
            'المشاريع',
            'حالة المشاريع',
            'المشاريع النشطة',
            'مشاريع مكتملة',
            'مهام المشروع',
            'مخاطر المشروع',
            'ميزانية المشروع',
            'تقدم المشروع',
            'كم مشروع لدينا',
            'المشاريع المتأخرة',
            'نسبة إنجاز المشاريع',
            'فريق المشروع',
            'تقرير المشاريع',
            'الجدول الزمني',
            'الموارد المطلوبة',
            'تكلفة المشروع',
            'المشاريع قيد التنفيذ',
            'مشروع جديد',
            'مواعيد التسليم',
            'المقاولات',
            'المناقصات',
        ],
        'pos_query': [
            'نقاط البيع',
            'الكاشير',
            'فاتورة مبيعات نقدية',
            'إيرادات نقطة البيع',
            'البيع المباشر',
            'السجل اليومي',
            'إغلاق الكاشير',
            'المنتجات الأكثر طلباً',
            'مبيعات الفرع',
            'الفاتورة',
            'الدفع نقداً',
            'الخزينة',
            'تحويل نقطة البيع',
            'كم مبيعات اليوم في المحل',
            'المرتجعات',
            'خصومات نقطة البيع',
        ],
        'payroll_query': [
            'الرواتب',
            'كشف الراتب',
            'قائمة الرواتب',
            'إجمالي الرواتب الشهرية',
            'البدلات والخصومات',
            'صافي الراتب',
            'إثبات الراتب',
            'كشف المرتبات',
            'رواتب الشهر الحالي',
            'كم إجمالي الرواتب',
            'الاستقطاعات',
            'التأمينات',
            'بدل السكن',
            'بدل النقل',
            'السلف',
            'المكافآت',
        ],
        'general_question': [
            'ما هو النظام',
            'كيف أستخدم النظام',
            'ما هي الميزات',
            'كيف يعمل النظام',
            'ما الفرق بين',
            'شرح',
            'مساعدة',
            'ساعدني',
            'أحتاج مساعدة',
            'لا أعرف',
            'كيف يمكنني',
            'هل يمكنني',
            'ما هي خطوات',
            'أين أجد',
            'ما هو',
            'ما هي',
            'لماذا',
            'كيف',
            'متى',
            'أين',
            'هل',
            'هل يوجد',
            'أريد أن',
            'أحتاج إلى',
            'ما هي وحدات النظام',
            'ماذا يقدم النظام',
        ],
    }

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 5),
            max_features=5000,
            sublinear_tf=True,
        )
        self.intent_vectors = None
        self._is_fitted = False

    def fit(self):
        """
        Train the classifier by fitting the TF-IDF vectorizer on the training data.
        Must be called before predict().
        """
        # Build the training corpus
        corpus = []
        intent_labels = []
        for intent, phrases in self.TRAINING_DATA.items():
            for phrase in phrases:
                corpus.append(phrase)
                intent_labels.append(intent)

        # Fit the vectorizer and transform the training data
        self.intent_vectors = self.vectorizer.fit_transform(corpus)
        self._intent_labels = intent_labels
        self._is_fitted = True

        logger.info(
            'IntentClassifier fitted with %d phrases across %d intents.',
            len(corpus),
            len(self.TRAINING_DATA),
        )

    def predict(self, text):
        """
        Predict the intent of a given text.

        Args:
            text (str): The user's message text.

        Returns:
            tuple: (intent_label: str, confidence: float)
                   intent_label is one of INTENT_LABELS.
                   confidence is between 0.0 and 1.0.
        """
        if not self._is_fitted:
            self.fit()

        if not text or not text.strip():
            return ('general_question', 0.0)

        # Vectorize the input text
        text_vector = self.vectorizer.transform([text.strip()])

        # Compute cosine similarity between input and all training phrases
        similarities = cosine_similarity(text_vector, self.intent_vectors).flatten()

        # Find the best matching intent
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        intent = self._intent_labels[best_idx]

        # Normalize the confidence score
        # Cosine similarity for TF-IDF is typically in [0, 1] range
        confidence = min(best_score, 1.0)

        logger.debug(
            'Intent prediction: "%s" -> %s (confidence: %.3f)',
            text[:50],
            intent,
            confidence,
        )

        return (intent, confidence)


# ── Module-level singleton instance ──────────────────────────────────────────
# Instantiate on module import; fit() is called lazily on first predict().
intent_classifier = IntentClassifier()

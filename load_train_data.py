import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, TrainingArguments, Trainer
import torch
import torch.nn.functional as F

class EmailDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(list(self.labels)[idx])
        return item


email_data = pd.read_csv('data/email_training_data.csv')

label_map = {
    'interview': 0,
    'offer': 1,
    'rejected': 2,
    'test': 3
}
email_updated_label = email_data.copy()
email_updated_label['label'] = email_data['label'].map(label_map)

train_texts, test_texts, train_labels, test_labels = train_test_split(
    email_updated_label['email_text'],
    email_updated_label['label'],
    test_size=0.2,
    random_state=42
)

print(f"Training set size: {len(train_texts)}")
print(f"Test set size: {len(test_texts)}")

print("Sample training data:", train_texts.head(5))
print("Sample training labels:", train_labels.head(5))


# So tokenising is like converting the texts into numbers and then distilbert has a
# classifer like a smal head over the entire model which will instruct how our small model wants to train that huge model to our need

tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=4 #num_labels=4 tells it "hey, you need to choose between 4 options" — that's literally the only customization needed here, everything else about DistilBERT's "brain" is already pre-built.
)
train_encodings = tokenizer(list(train_texts), truncation=True, padding=True)
test_encodings = tokenizer(list(test_texts), truncation=True, padding=True)

train_dataset = EmailDataset(train_encodings, train_labels)
test_dataset = EmailDataset(test_encodings, test_labels)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=4,
    per_device_train_batch_size=8,
    eval_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset
)

trainer.train()


# NOTES:
# Think of this as teaching a smart intern (DistilBERT) a new specific skill, in stages:

# 1. Get the study material ready (pandas + train_test_split)
# You load your 53 emails, convert their text labels (interview/rejected/etc) into numbers (since the model only understands numbers), then split into a study deck (42 emails, for teaching) and a pop quiz deck (11 emails, to check if it actually learned, not just memorized). Why split? So you can honestly test if it generalized, not just parroted answers.

# 2. Hire the intern + give them a translator (tokenizer + model)
# DistilBertTokenizer = a translator that turns English sentences into number-code the intern understands. DistilBertForSequenceClassification = the intern itself — already smart about language in general (pre-trained), but doesn't yet know YOUR specific task. num_labels=4 tells the intern "you'll be sorting things into 4 buckets," and it builds a tiny "decision-maker" on top just for that.

# 3. Translate the study material (tokenizing train/test texts)
# Before the intern can study, ALL the emails need to go through the translator first — train_encodings and test_encodings are your emails, now in number-code, ready to be studied.

# 4. Make flashcards (EmailDataset)
# As we covered — package each translated email together WITH its correct answer, so each flashcard is self-contained: "here's the email in number form, here's the right label." One deck for studying, one for quizzing.

# 5. Set study rules (TrainingArguments)
# num_train_epochs=4 = "go through the whole study deck 4 times." per_device_train_batch_size=8 = "look at 8 flashcards at once before adjusting your understanding a little" (more stable than one at a time). eval_strategy="epoch" = "after each full pass through the study deck, quiz yourself on the pop quiz deck, and tell me the score" — so you can watch it improve (or not) across each pass.

# 6. Actually study (Trainer + trainer.train())
# Trainer bundles the intern + rules + both decks together into one coordinator. trainer.train() is the "go!" button — it now actually runs the real teach-quiz-adjust loop, 4 times through, and adjusts the intern's tiny decision-maker each round to get better at YOUR specific 4-way sorting task.

predictions = trainer.predict(test_dataset)
# predicted_labels = predictions.predictions.argmax(axis=1)
# print("Predicted:", list(predicted_labels))
# print("Actual:   ", list(test_labels))


logits = torch.tensor(predictions.predictions)
probabilities = F.softmax(logits, dim=1)

confidence_scores, predicted_labels = torch.max(probabilities, dim=1)

# 25% = the random-guessing floor (math, not our choice). 
# 35% = our chosen threshold, deliberately set a bit ABOVE that floor, 
# so "confident" actually means something better than a coin flip, 
# not just AT the coin flip level
CONFIDENCE_THRESHOLD = 0.35

for i in range(len(test_texts)):
    label = predicted_labels[i].item()
    confidence = confidence_scores[i].item()
    
    if confidence < CONFIDENCE_THRESHOLD:
        print(f"⚠️ NEEDS REVIEW (confidence: {confidence:.2f}) — guessed label: {label}")
    else:
        print(f"✅ Confident (confidence: {confidence:.2f}) — predicted label: {label}")


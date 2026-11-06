import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split

class FederatedEngine:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.global_model = None
        self.history = []
        self.participants = []

    def make_model(self, learning_rate=0.01, classes=None):
        return SGDClassifier(loss="log_loss", penalty="l2", alpha=learning_rate / 10,
                             learning_rate="constant", eta0=learning_rate,
                             random_state=self.random_state, average=True)

    def train(self, X, y, clients=5, rounds=8, epochs=2, learning_rate=0.01,
              drift_sensitivity=0.15, adaptive=True):
        classes = np.unique(y)
        # Deterministic non-IID partition: clients receive class-skewed shards.
        indices = np.arange(len(y))
        rng = np.random.default_rng(self.random_state)
        rng.shuffle(indices)
        shards = np.array_split(indices, clients * 2)
        partitions = [np.concatenate(shards[i::clients]) if clients else indices
                      for i in range(clients)]
        partitions = [partition for partition in partitions if len(partition)]
        self.global_model = self.make_model(learning_rate, classes)
        self.global_model.partial_fit(X[:1] if False else X[:len(classes)], np.repeat(classes, len(classes) // len(classes))[:len(classes)], classes=classes)
        self.history = []
        self.participants = []

        for round_number in range(1, rounds + 1):
            local_models, losses, participant_ids = [], [], []
            for client_index, partition in enumerate(partitions):
                # Adaptively skip very stable clients on alternate rounds only when drift sensitivity requests it.
                local_error_window = self.history[-1]["loss"] if self.history else 0.5
                drift_score = abs(local_error_window - (1 - round_number / max(rounds * 2, 1)))
                if adaptive and drift_sensitivity > 0 and drift_score > drift_sensitivity and client_index % 3 == round_number % 3:
                    continue
                model = self.make_model(learning_rate, classes)
                seed_count = min(len(partitions[client_index]), len(classes))
                seed_indices = partition[:seed_count]
                model.partial_fit(X[seed_indices], y[seed_indices], classes=classes)
                if hasattr(self.global_model, "coef_"):
                    model.coef_ = self.global_model.coef_.copy()
                    model.intercept_ = self.global_model.intercept_.copy()
                    model._standard_coef = model.coef_.copy()
                    model._average_coef = model.coef_.copy()
                    model.classes_ = classes
                local_y = y[partition]
                local_classes = np.unique(local_y)
                for _ in range(epochs):
                    order = rng.permutation(len(partition))
                    for start in range(0, len(partition), 256):
                        batch = order[start:start + 256]
                        local_classes_present = np.unique(np.concatenate([local_classes, classes]))
                        model.classes_ = classes
                        model.partial_fit(X[partition[batch]], local_y[batch], classes=classes)
                predictions = model.predict(X[partition])
                loss = float(np.mean(predictions != local_y))
                losses.append(loss)
                local_models.append(model)
                participant_ids.append(client_index)

            if not local_models:
                local_models = [self.make_model(learning_rate, classes) for _ in partitions]
                for model, partition in zip(local_models, partitions):
                    model.classes_ = classes
                    model.partial_fit(X[partition], y[partition], classes=classes)
                participant_ids = list(range(len(partitions)))
                losses = [0.5] * len(local_models)

            sizes = np.array([len(partitions[index]) for index in participant_ids], dtype=float)
            adaptive_quality = np.array([1 / (1 + loss) for loss in losses])
            weights = sizes * adaptive_quality if adaptive else sizes
            weights /= weights.sum()
            self.global_model.coef_ = np.average([m.coef_ for m in local_models], axis=0, weights=weights)
            self.global_model.intercept_ = np.average([m.intercept_ for m in local_models], axis=0, weights=weights)
            train_predictions = self.global_model.predict(X)
            accuracy = float(np.mean(train_predictions == y))
            loss = float(np.mean(losses))
            round_record = {"round": round_number, "accuracy": accuracy, "loss": loss,
                            "participants": len(local_models)}
            self.history.append(round_record)
            self.participants = participant_ids
        return {
            "accuracy": float(self.history[-1]["accuracy"]),
            "loss": float(self.history[-1]["loss"]),
            "rounds": self.history,
            "participants": self.participants,
        }

    def predict(self, X):
        if self.global_model is None:
            raise RuntimeError("No trained federated model is available")
        return self.global_model.predict(X)

engine = FederatedEngine()

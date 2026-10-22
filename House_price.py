import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LinearRegression, Lasso, Ridge
from sklearn.svm import SVR
from sklearn.inspection import permutation_importance
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

rf = pd.read_csv("train (1).csv")

print("\n" + "=" * 70)
print("Head")
print(rf.head())
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("info")
print(rf.info())
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("columns")
print(rf.columns.tolist())
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("Dtypes")
print(rf.dtypes)
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("Missing_values")
print(rf.isnull().sum())
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("Total Missing_values")
print(rf.isnull().sum().sum())
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("nPercnetages Of Missing_values")
print(rf.isnull().sum() / len(rf) * 100)
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("Duplicates")
print(rf.duplicated().sum())
print("\n" + "=" * 70)

print("\n" + "=" * 70)
print("Description")
print(rf.describe())
print("\n" + "=" * 70)

cat_cols = rf.select_dtypes(include=["object", "category"]).columns.tolist()
for c in cat_cols:
    print("\n" + "=" * 70)
    print("Categorical Analysis:")
    print("\n" + "=" * 70)
    print(rf[c].value_counts())
    print(c, rf[c].nunique(), rf[c].unique()[:10])

numeric_cols = rf.select_dtypes(include=["number"]).columns.tolist()
for col in numeric_cols:
    print("\n" + "=" * 70)
    print("Numeric and Outliers Analysis:")
    print("\n" + "=" * 70)

    Q1 = rf[col].quantile(0.25)
    Q3 = rf[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = ((rf[col] < lower) | (rf[col] > upper)).sum()

    print(
        f"Count     :{rf[col].count()}\n"
        f"Missing   :{rf[col].isnull().sum()}\n"
        f"Mean      :{rf[col].mean()}\n"
        f"Median    :{rf[col].median()}\n"
        f"Max       :{rf[col].max()}\n"
        f"Min       :{rf[col].min()}\n"
        f"Std       :{rf[col].std()}\n"
        f"Outlier   :{outliers}"
    )

for col in numeric_cols:
    plt.figure(figsize=(8, 5))
    plt.hist(rf[col].dropna(), bins=20)
    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.close()


pd.set_option("display.max_rows", None)
corr = rf[numeric_cols].corr()["SalePrice"]
strong_corr = corr[(abs(corr) >= 0.45) & (corr.index != "SalePrice")]
print(strong_corr)

selected_features = [
    "OverallQual",
    "YearBuilt",
    "YearRemodAdd",
    "MasVnrArea",
    "TotalBsmtSF",
    "1stFlrSF",
    "GrLivArea",
    "FullBath",
    "TotRmsAbvGrd",
    "Fireplaces",
    "GarageYrBlt",
    "GarageCars",
    "GarageArea",
]


x = rf[selected_features]
y = rf["SalePrice"]

categori_cols = x.select_dtypes(include=["category", "object"]).columns.tolist()

numeric_colss = x.select_dtypes(include=["number"]).columns.tolist()

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            Pipeline(
                [
                    ("imput", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            ),
            numeric_colss,
        ),
        (
            "cat",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore")),
                ]
            ),
            categori_cols,
        ),
    ]
)


x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42
)

models = {
    "Linear": LinearRegression(),
    "SVR": SVR(),
    "RandomF": RandomForestRegressor(),
    "Lasso": Lasso(),
    "Ridge": Ridge(),
}
result = []

for name, model in models.items():
    pip = Pipeline(steps=[("prep", preprocessor), ("model", model)])

    pip.fit(x_train, y_train)
    prediction = pip.predict(x_test)

    result.append(
        {
            "Model": name,
            "R2": r2_score(y_test, prediction),
            "MAE": mean_absolute_error(y_test, prediction),
            "Rmse": root_mean_squared_error(y_test, prediction),
        }
    )

result_df = pd.DataFrame(result)
print(result_df)


testing_model = Pipeline(
    steps=[("prep", preprocessor), ("model", RandomForestRegressor(random_state=42))]
)

param_grid = {
    "model__n_estimators": [200, 300, 500],
    "model__max_depth": [None, 10, 20, 30],
    "model__min_samples_split": [2, 5, 10],
    "model__min_samples_leaf": [1, 2, 4],
    "model__max_features": [1.0, "sqrt", 0.5],
}

# grid=GridSearchCV(
#     testing_model,
#     param_grid,
#     cv=5,
#     scoring='r2'
# )

# grid.fit(x_train,y_train)
# print(
#     f"Best_params    :{grid.best_params_}\n"
#     f"Best_score     :{grid.best_score_}\n"
#     f"Best_estimator :{grid.best_estimator_}"
# )


best_list = []

best_model = Pipeline(
    steps=[
        ("prep", preprocessor),
        (
            "model",
            RandomForestRegressor(
                max_depth=10,
                max_features="sqrt",
                min_samples_leaf=2,
                min_samples_split=5,
                n_estimators=200,
                random_state=42,
            ),
        ),
    ]
)

scores = cross_val_score(best_model, x_train, y_train, cv=5, scoring="r2")
print(
    f"score   :{scores}\n"
    f"mean    :{scores.mean():.2f}\n"
    f"std     :{scores.std():.2f}"
)
best_model.fit(x_train, y_train)
##Variance/Bias

train_pred = best_model.predict(x_train)
test_pred = best_model.predict(x_test)
train_acc = r2_score(y_train, train_pred)
test_acc = r2_score(y_test, test_pred)
print(f"TRAINED :{train_acc:.2f}\n" f"TESTED  :{test_acc:.2F}")

labels = ["Testing", "Training"]
scores = [train_acc, test_acc]
plt.bar(labels, scores)
plt.ylim(0, 1)
plt.title("Accuracy")
plt.close()

y_pred = pip.predict(x_test)

comparison = pd.DataFrame({"Actual": y_test, "Predicted": y_pred})

print(comparison.head(10))

# plot#
plt.figure(figsize=(10, 5))
sns.scatterplot(x=y_test, y=y_pred)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "--r")
plt.title("Actual Vs Predicted")
plt.xlabel("Actual")
plt.ylabel("Predicted")
plt.show()

# residual#
residual = y_test - y_pred
sns.scatterplot(x=y_pred, y=residual)
plt.axhline(y=0)
plt.show()

best_list.append(
    {
        "Model": "RandomForestRegressor",
        "R2": r2_score(y_test, y_pred),
        "MAE": mean_absolute_error(y_test, y_pred),
        "Rmse": root_mean_squared_error(y_test, y_pred),
    }
)

best_df = pd.DataFrame(best_list)
print(best_df)


features = best_model.named_steps["prep"].get_feature_names_out()
cofficion = best_model.named_steps["model"].feature_importances_

imp = pd.DataFrame({"feature": features, "importance": cofficion * 100}).sort_values(
    by="importance", ascending=False
)

print(imp.head(10))


perm = permutation_importance(
    best_model, x_test, y_test, n_repeats=5, random_state=42, scoring="r2"
)

result = pd.DataFrame(
    {"feature": x_test.columns, "importance": perm.importances_mean * 100}
).sort_values(by="importance", ascending=False)
print(result.head(10))


app_cols = [
    "OverallQual",
    "YearBuilt",
    "YearRemodAdd",
    "GrLivArea",
    "TotalBsmtSF",
    "GarageCars",
    "FullBath",
    "TotRmsAbvGrd",
]

x = rf[app_cols]
y = rf["SalePrice"]

categori_cols = x.select_dtypes(include=["category", "object"]).columns.tolist()

numeric_colss = x.select_dtypes(include=["number"]).columns.tolist()

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            Pipeline(
                [
                    ("imput", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            ),
            numeric_colss,
        ),
        (
            "cat",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore")),
                ]
            ),
            categori_cols,
        ),
    ]
)


x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42
)


final_list = []

final_model = Pipeline(
    steps=[
        ("prep", preprocessor),
        (
            "model",
            RandomForestRegressor(
                max_depth=20,
                max_features="sqrt",
                min_samples_leaf=1,
                min_samples_split=2,
                n_estimators=200,
                random_state=42,
            ),
        ),
    ]
)


final_model.fit(x_train, y_train)
import joblib

joblib.dump(final_model,"house.pkl")


y_pred = final_model.predict(x_test)

comparison = pd.DataFrame({"Actual": y_test, "Predicted": y_pred})

print(comparison.head(10))

# plot#
plt.figure(figsize=(10, 5))
sns.scatterplot(x=y_test, y=y_pred)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "--r")
plt.title("Actual Vs Predicted")
plt.xlabel("Actual")
plt.ylabel("Predicted")
plt.show()


final_list.append(
    {
        "Model": "RandomForestRegressor",
        "R2": r2_score(y_test, y_pred),
        "MAE": mean_absolute_error(y_test, y_pred),
        "Rmse": root_mean_squared_error(y_test, y_pred),
    }
)

final_df = pd.DataFrame(final_list)
print(final_df)

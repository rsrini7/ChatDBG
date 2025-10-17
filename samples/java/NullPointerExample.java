/**
 * Sample Java program demonstrating common null pointer exception scenarios
 * for ChatDBG JDB integration testing.
 */

import java.util.List;
import java.util.ArrayList;

public class NullPointerExample {

    private String name;
    private List<String> items;

    public NullPointerExample(String name) {
        this.name = name;
        // items is not initialized - potential null pointer source
    }

    public void addItem(String item) {
        if (item != null) {
            if (this.items == null) {
                this.items = new ArrayList<>();
            }
            this.items.add(item);
        }
    }

    public String getName() {
        return name; // Could be null if not set
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<String> getItems() {
        return items; // Could be null
    }

    public String processItems() {
        if (this.items == null) {
            return "No items to process";
        }

        StringBuilder result = new StringBuilder();
        for (String item : this.items) {
            result.append(item.toUpperCase()); // Null pointer if item is null
            result.append(" ");
        }

        return result.toString().trim();
    }

    public static void main(String[] args) {
        System.out.println("Starting NullPointerExample...");

        NullPointerExample example = new NullPointerExample("Test");

        // This will cause a null pointer exception
        example.addItem("first");
        example.addItem(null); // This null will cause NPE in processItems()
        example.addItem("third");

        try {
            String result = example.processItems();
            System.out.println("Result: " + result);
        } catch (NullPointerException e) {
            System.err.println("Caught NullPointerException: " + e.getMessage());
            throw e; // Re-throw to trigger debugger
        }

        System.out.println("Program completed successfully");
    }
}